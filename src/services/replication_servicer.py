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

    def __init__(self, replica):
        self.replica = replica

    def Heartbeat(self, request, context):
        logger.warning("Heartbeat not implemented yet")

    def ReplicateOperation(self, request, context):
        logger.warning("ReplicateOperation not implemented yet")

    def JoinNetwork(self, request, context):
        """Handle a new server joining the network."""
        new_server_id = request.server_id
        new_server_address = request.address

        logger.info(
            f"Received join request from {new_server_id} at {new_server_address}"
        )

        # Only the leader can add new servers
        if self.replica.role != "leader":
            if self.replica.leader_id and self.replica.leader_id in self.replica.peers:
                # Forward to leader
                try:
                    leader_address = self.replica.peers[self.replica.leader_id]
                    with grpc.insecure_channel(leader_address) as channel:
                        stub = replication_grpc.ReplicationServiceStub(channel)
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
            new_server_id in self.replica.peers
            and self.replica.peers[new_server_id] != new_server_address
        ):
            logger.warning(
                f"Server {new_server_id} already exists with a different address. Updating to {new_server_address}"
            )

        # Check if the address already exists with a different ID
        address_to_id = {addr: id for id, addr in self.replica.peers.items()}
        if (
            new_server_address in address_to_id
            and address_to_id[new_server_address] != new_server_id
        ):
            existing_id = address_to_id[new_server_address]
            logger.warning(
                f"Address {new_server_address} already registered with server ID {existing_id}. Removing {existing_id}."
            )

            # Remove the old server ID that was using this address
            del self.replica.peers[existing_id]
            if existing_id in self.replica.servers_info:
                del self.replica.servers_info[existing_id]

        # Add the new server to peers
        self.replica.peers[new_server_id] = new_server_address

        # Add to servers info
        self.replica.servers_info[new_server_id] = replication.ServerInfo(
            server_id=new_server_id, address=new_server_address, role="follower"
        )

        logger.info(f"Added new server {new_server_id} to the network")

        # Create server addresses mapping
        server_addresses = {}
        for server_id, address in self.replica.peers.items():
            server_addresses[server_id] = address
        server_addresses[self.replica.server_id] = self.replica.address

        # Create response with current network state
        return replication.JoinResponse(
            success=True,
            servers=list(self.replica.servers_info.values()),
            leader_id=self.replica.server_id,
            term=self.replica.term,
            server_addresses=server_addresses,
        )

    def GetNetworkState(self, request, context):
        """Return the current state of the network."""
        logger.info(f"Received network state request from {request.server_id}")

        return replication.NetworkStateResponse(
            servers=list(self.replica.servers_info.values()),
            leader_id=self.replica.leader_id if self.replica.leader_id else "",
            term=self.replica.term,
        )
