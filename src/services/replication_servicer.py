"""
ReplicationService implementation for handling replication and consensus between
server replicas.
"""

import grpc
import logging

from src.protocol.grpc import replication_pb2 as replication
from src.protocol.grpc import replication_pb2_grpc


logger = logging.getLogger(__name__)


class ReplicationServicer(replication_pb2_grpc.ReplicationServiceServicer):
    """Replication service implementation for handling replication"""

    def __init__(self, replica, chat_servicer=None):
        self.replica = replica
        self.replica_state = replica.state
        self.chat_servicer = chat_servicer

    def Heartbeat(self, request, context):
        """Process heartbeat from another server."""
        # Reset election timer on receiving heartbeat
        self.replica.election_manager.reset_election_timer()

        peer_id = request.server_id
        peer_term = request.term
        peer_role = request.role

        # Update peer info
        if peer_id not in self.replica_state.servers_info:
            if peer_id in self.replica_state.peers:
                peer_address = self.replica_state.peers[peer_id]
                self.replica_state.servers_info[peer_id] = replication.ServerInfo(
                    server_id=peer_id, address=peer_address, role=peer_role
                )
        else:
            self.replica_state.servers_info[peer_id].role = peer_role

        # If the peer has a higher term, update our term and become follower
        if peer_term > self.replica_state.term:
            logger.info(
                f"Discovered higher term {peer_term} from {peer_id}, updating term and becoming follower"
            )
            self.replica_state.term = peer_term
            self.replica_state.role = "follower"
            self.replica_state.voted_for = None

            # If peer is a leader, update leader_id
            if peer_role == "leader":
                self.replica_state.leader_id = peer_id

        # If peer is a candidate requesting vote
        if peer_role == "candidate" and peer_term == self.replica_state.term:
            # Vote for the candidate if we haven't voted yet in this term
            if self.replica_state.voted_for is None:
                self.replica_state.voted_for = peer_id
                logger.info(f"Voting for {peer_id} in term {peer_term}")
                return replication.HeartbeatResponse(
                    success=True,
                    server_id=self.replica_state.server_id,
                    term=self.replica_state.term,
                    role=self.replica_state.role,
                )

        # If peer is a leader and term is valid, acknowledge leadership
        if peer_role == "leader" and peer_term >= self.replica_state.term:
            if self.replica_state.leader_id != peer_id:
                logger.info(f"Acknowledging {peer_id} as leader for term {peer_term}")
                self.replica_state.leader_id = peer_id
                self.replica_state.role = "follower"
                self.replica_state.term = peer_term
                self.replica_state.voted_for = None

        return replication.HeartbeatResponse(
            success=True,
            server_id=self.replica_state.server_id,
            term=self.replica_state.term,
            role=self.replica_state.role,
        )

    def JoinNetwork(self, request, context):
        """Handle a new server joining the network."""
        new_server_id = request.server_id
        new_server_address = request.address

        logger.info(
            f"Received join request from {new_server_id} at {new_server_address}"
        )

        # Only the leader can add new servers
        if self.replica_state.role != "leader":
            if (
                self.replica_state.leader_id
                and self.replica_state.leader_id in self.replica_state.peers
            ):
                # Forward to leader
                try:
                    leader_address = self.replica_state.peers[
                        self.replica_state.leader_id
                    ]
                    with grpc.insecure_channel(leader_address) as channel:
                        stub = replication_pb2_grpc.ReplicationServiceStub(channel)
                        return stub.JoinNetwork(request)
                except Exception as e:
                    logger.error(f"Error forwarding join request to leader: {str(e)}")
                    context.set_code(grpc.StatusCode.UNAVAILABLE)
                    context.set_details("Leader unavailable. Try again later.")
                    return replication.JoinResponse(success=False)
            else:
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details(
                    "Cannot process join request: not the leader and no leader known"
                )
                return replication.JoinResponse(success=False)

        # Check if the server ID already exists but with a different address
        if (
            new_server_id in self.replica_state.peers
            and self.replica_state.peers[new_server_id] != new_server_address
        ):
            logger.warning(
                f"Server {new_server_id} already exists with a different address. Updating to {new_server_address}"
            )

        # Check if the address already exists with a different ID
        address_to_id = {addr: id for id, addr in self.replica_state.peers.items()}
        if (
            new_server_address in address_to_id
            and address_to_id[new_server_address] != new_server_id
        ):
            existing_id = address_to_id[new_server_address]
            logger.warning(
                f"Address {new_server_address} already registered with server ID {existing_id}. Removing {existing_id}."
            )

            # Remove the old server ID that was using this address
            del self.replica_state.peers[existing_id]
            if existing_id in self.replica_state.servers_info:
                del self.replica_state.servers_info[existing_id]

        # Add the new server to peers
        self.replica_state.peers[new_server_id] = new_server_address

        # Add to servers info
        self.replica_state.servers_info[new_server_id] = replication.ServerInfo(
            server_id=new_server_id, address=new_server_address, role="follower"
        )

        logger.info(f"Added new server {new_server_id} to the network")

        # Create server addresses mapping
        server_addresses = {}
        for server_id, address in self.replica_state.peers.items():
            server_addresses[server_id] = address
        server_addresses[self.replica_state.server_id] = self.replica_state.address

        # Create response with current network state
        return replication.JoinResponse(
            success=True,
            servers=list(self.replica_state.servers_info.values()),
            leader_id=self.replica_state.server_id,
            term=self.replica_state.term,
            server_addresses=server_addresses,
        )

    def GetNetworkState(self, request, context):
        """Return the current state of the network."""
        logger.info(f"Received network state request from {request.server_id}")

        return replication.NetworkStateResponse(
            servers=list(self.replica_state.servers_info.values()),
            leader_id=(
                self.replica_state.leader_id if self.replica_state.leader_id else ""
            ),
            term=self.replica_state.term,
        )

    def ReplicateOperation(self, request, context):
        """Handle replicated operations from the leader"""
        try:
            service_name = request.service_name
            method_name = request.method_name
            serialized_request = request.serialized_request
            operation_id = request.operation_id

            logger.info(
                f"Received replicated operation: {service_name}.{method_name} (ID: {operation_id})"
            )

            # Create a dummy context
            class DummyContext:
                def set_code(self, code):
                    pass

                def set_details(self, details):
                    pass

            dummy_context = DummyContext()

            # Get the appropriate service
            service = None
            if service_name == "ChatServicer":
                service = self.chat_servicer
            else:
                logger.error(f"Unknown service: {service_name}")
                return replication.OperationResponse(
                    success=False, server_id=self.replica_state.server_id
                )

            # Deserialize the request based on service and method
            request_obj = self._deserialize_request(
                service_name, method_name, serialized_request
            )
            if not request_obj:
                logger.error(
                    f"Failed to deserialize request for {service_name}.{method_name}"
                )
                return replication.OperationResponse(
                    success=False, server_id=self.replica_state.server_id
                )

            # Call the method without triggering replication
            success = self._execute_without_replication(
                service, method_name, request_obj, dummy_context
            )

            logger.info(
                f"Successfully processed replicated operation: {service_name}.{method_name} (ID: {operation_id})"
            )

            return replication.OperationResponse(
                success=success, server_id=self.replica_state.server_id
            )

        except Exception as e:
            logger.error(f"Error processing replicated operation: {str(e)}")
            return replication.OperationResponse(
                success=False, server_id=self.replica_state.server_id
            )

    def _deserialize_request(self, service_name, method_name, serialized_request):
        """Deserialize request based on service and method name"""
        from src.protocol.grpc import chat_pb2

        # Map for ChatServicer methods
        if service_name == "ChatServicer":
            request_classes = {
                "Signup": chat_pb2.SignupRequest,
                "Login": chat_pb2.LoginRequest,
                "DeleteUser": chat_pb2.DeleteUserRequest,
                "GetUserMessageLimit": chat_pb2.GetUserMessageLimitRequest,
                "SaveSettings": chat_pb2.SaveSettingsRequest,
                "GetUsersToDisplay": chat_pb2.GetUsersToDisplayRequest,
                "GetChats": chat_pb2.GetChatsRequest,
                "StartChat": chat_pb2.StartChatRequest,
                "GetMessages": chat_pb2.GetMessagesRequest,
                "SendChatMessage": chat_pb2.SendMessageRequest,
                "DeleteMessages": chat_pb2.DeleteMessagesRequest,
            }

            if method_name in request_classes:
                request_class = request_classes[method_name]
                request_obj = request_class()
                request_obj.ParseFromString(serialized_request)
                return request_obj

        return None

    def _execute_without_replication(self, service, method_name, request_obj, context):
        """Execute a method without triggering replication"""
        try:
            # Check if the method exists
            if not hasattr(service, method_name):
                logger.error(f"Method {method_name} not found on service")
                return False

            method = getattr(service, method_name)

            # Temporarily disable replication
            original_replica = service.replica
            try:
                # the evil move lol
                service.replica = None
                method(request_obj, context)
                return True
            finally:
                # Rerestore the replica
                service.replica = original_replica
        except Exception as e:
            logger.error(f"Error executing method {method_name}: {str(e)}")
            return False
