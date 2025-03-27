import grpc
import logging
import threading
from typing import Dict, List, Optional

from src.protocol.grpc import replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc
from src.protocol.grpc.chat_pb2_grpc import ChatServiceServicer as ChatService

from .replica_state import ReplicaState
from .election_manager import ElectionManager
from .heartbeat_manager import HeartbeatManager
from .replication_manager import ReplicationManager

logger = logging.getLogger(__name__)


class ReplicaNode:
    """
    Main Implementation of the replica state and operations
    """

    def __init__(self, server_id: str, address: str, peers: List[str] = None):
        # Initialize the node state
        self.state = ReplicaState(server_id, address, peers)

        # Initialize specialized managers
        self.election_manager = ElectionManager(self.state)
        self.heartbeat_manager = HeartbeatManager(self.state)
        self.replication_manager = ReplicationManager(self.state)

        # Set up cross-references between managers
        self.heartbeat_manager.set_election_manager(self.election_manager)

        # Thread control
        self.is_running = False
        self.heartbeat_thread = None

    def start(self):
        """Start this replica operations."""
        self.is_running = True
        self.state.is_running = True

        # Start election timer
        self.election_manager.reset_election_timer()

        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(
            target=self.heartbeat_manager.heartbeat_loop
        )
        self.heartbeat_thread.daemon = True
        self.heartbeat_thread.start()

        # If we have peers, try to join the network
        if self.state.peers:
            self.join_network()
        else:
            # If no peers, become the initial leader
            self.election_manager.become_leader()
            logger.info(
                f"No peers provided. {self.state.server_id} is the initial leader."
            )
            self.state.servers_info[self.state.server_id] = replication.ServerInfo(
                server_id=self.state.server_id,
                address=self.state.address,
                role="leader",
            )

    def shutdown(self):
        """Shutdown this replica."""
        self.is_running = False
        self.state.is_running = False
        self.election_manager.cancel_election_timer()

    def check_leader_status(self):
        """Check if the current leader is still available."""
        return self.heartbeat_manager.check_leader_status()

    def replicate_to_followers(self, service_name, method_name, serialized_request):
        """Replicate an operation to all followers."""
        operation_id = self.get_next_operation_id()

        # -------------------
        logger.info("Replicating %s.%s", service_name, method_name)

        # If we're the leader, replicate to followers
        if self.state.role == "leader":
            self.state.last_operation_id += 1
            operation_id = self.state.last_operation_id

            self.replication_manager.replicate_to_followers(
                service_name,
                method_name,
                serialized_request,
                operation_id,
            )

            return True

        # If we're a follower, forward to leader
        elif (
            self.state.role == "follower"
            and self.state.leader_id
            and self.state.leader_id in self.state.peers
        ):
            logger.warning(
                "TODO: Forwarding replication to leader from a follower NOT IMPLEMENTED yet. For now, client should retry other peers."
            )
            return False

        # No known leader or couldn't contact leader, process locally
        logger.info(
            f"No known leader or leader unavailable. We'll let caller process this locally as: {self.role}"
        )
        logger.info("Also, we'll take on leader from now on.")
        # set ourselves as the leader
        self.election_manager.become_leader()
        return True

    def log_operation(self, service, method, parameters, result, operation_id):
        """Log an operation to the operation log."""
        self.replication_manager.log_operation(
            service, method, parameters, result, operation_id
        )

    def get_next_operation_id(self):
        """Get the next operation ID."""
        return self.replication_manager.get_next_operation_id()

    def join_network(self):
        """Join the existing network by contacting a peer."""
        joined = False

        for peer_id, peer_address in self.state.peers.items():
            try:
                with grpc.insecure_channel(peer_address) as channel:
                    stub = replication_grpc.ReplicationServiceStub(channel)

                    request = replication.JoinRequest(
                        server_id=self.state.server_id, address=self.state.address
                    )

                    response = stub.JoinNetwork(request, timeout=5)

                    if response.success:
                        joined = True
                        self.state.term = response.term
                        self.state.leader_id = response.leader_id

                        # Clear existing peers to avoid duplicates
                        self.state.peers = {}
                        self.state.servers_info = {}

                        # Track addresses to avoid adding duplicates
                        address_to_id = {}

                        # Update peers list with all servers in the network
                        for server in response.servers:
                            if server.server_id != self.state.server_id:
                                # Skip duplicate addresses
                                if server.address in address_to_id:
                                    logger.warning(
                                        f"Skipping duplicate server {server.server_id} with address {server.address} (already mapped to {address_to_id[server.address]})"
                                    )
                                    continue

                                self.state.peers[server.server_id] = server.address
                                self.state.servers_info[server.server_id] = server
                                address_to_id[server.address] = server.server_id

                        # Update server addresses from the map
                        for server_id, address in response.server_addresses.items():
                            if server_id != self.state.server_id:
                                # Skip duplicate addresses
                                if (
                                    address in address_to_id
                                    and address_to_id[address] != server_id
                                ):
                                    logger.warning(
                                        f"Skipping duplicate server {server_id} with address {address} (already mapped to {address_to_id[address]})"
                                    )
                                    continue

                                self.state.peers[server_id] = address
                                address_to_id[address] = server_id

                        logger.info(
                            f"Successfully joined the network through {peer_id}"
                        )
                        logger.info(
                            f"Current leader is {self.state.leader_id} with term {self.state.term}"
                        )
                        logger.info(f"Network peers: {self.state.peers}")

                        # Add self to servers info
                        self.state.servers_info[self.state.server_id] = (
                            replication.ServerInfo(
                                server_id=self.state.server_id,
                                address=self.state.address,
                                role="follower",
                            )
                        )

                        # Reset election timer
                        if self.election_manager:
                            self.election_manager.reset_election_timer()
                        # break
            except Exception as e:
                logger.error(f"Failed to join network through {peer_id}: {str(e)}")

        if not joined:
            logger.warning(
                "Failed to join network through any peer. Starting as leader."
            )
            if self.election_manager:
                self.election_manager.become_leader()
