import grpc
import logging
from typing import Dict, List, Tuple

from src.protocol.grpc import replication_pb2 as replication
from src.protocol.grpc import replication_pb2_grpc as replication_grpc

logger = logging.getLogger(__name__)


class ReplicaNode:
    """
    Implementation of the replica state and operations
    """

    def __init__(self, server_id: str, address: str, peers: List[str] = None):
        self.server_id = server_id
        self.address = address

        # Initialize server state
        self.term = 0
        self.role = "follower"  # Start as follower
        self.leader_id = None
        self.peers: Dict[str, str] = {}  # server_id -> address mapping
        self.servers_info: Dict[str, replication.ServerInfo] = {}  # All server info

        if peers:
            for peer in peers:
                # peer format is "server_id:address"
                if ":" in peer and peer.count(":") == 2:
                    peer_id, peer_address = peer.split(":", 1)
                    self.peers[peer_id] = peer_address
                else:
                    # direct address format
                    self.peers[f"peer_{len(self.peers)}"] = peer

        # Initialize own server info
        self.servers_info[self.server_id] = replication.ServerInfo(
            server_id=self.server_id, address=self.address, role="follower"
        )

    def start(self):
        logger.info(f"Initializing replica node {self.server_id}...")
        if self.peers:
            self.join_network()
        else:
            self.become_leader()
            logger.info(f"No peers provided. {self.server_id} is the initial leader.")
            self.servers_info[self.server_id] = replication.ServerInfo(
                server_id=self.server_id, address=self.address, role="leader"
            )

    def shutdown(self):
        logger.warning("TODO: shutdown not implemented yet")

    def become_leader(self):
        logger.warning("TODO: become_leader not implemented yet")

    def join_network(self):
        """Join the existing network by contacting a peer."""
        joined = False

        for peer_id, peer_address in self.peers.items():
            try:
                with grpc.insecure_channel(peer_address) as channel:
                    stub = replication_grpc.ReplicationServiceStub(channel)

                    request = replication.JoinRequest(
                        server_id=self.server_id, address=self.address
                    )

                    response = stub.JoinNetwork(request, timeout=5)

                    if response.success:
                        joined = True
                        self.term = response.term
                        self.leader_id = response.leader_id

                        # Clear existing peers to avoid duplicates
                        self.peers = {}
                        self.servers_info = {}

                        # Track addresses to avoid adding duplicates
                        address_to_id = {}

                        # Update peers list with all servers in the network
                        for server in response.servers:
                            if server.server_id != self.server_id:
                                # Skip duplicate addresses
                                if server.address in address_to_id:
                                    logger.warning(
                                        f"Skipping duplicate server {server.server_id} with address {server.address} (already mapped to {address_to_id[server.address]})"
                                    )
                                    continue

                                self.peers[server.server_id] = server.address
                                self.servers_info[server.server_id] = server
                                address_to_id[server.address] = server.server_id

                        # Update server addresses from the map
                        for server_id, address in response.server_addresses.items():
                            if server_id != self.server_id:
                                # Skip duplicate addresses
                                if (
                                    address in address_to_id
                                    and address_to_id[address] != server_id
                                ):
                                    logger.warning(
                                        f"Skipping duplicate server {server_id} with address {address} (already mapped to {address_to_id[address]})"
                                    )
                                    continue

                                self.peers[server_id] = address
                                address_to_id[address] = server_id

                        logger.info(
                            f"Successfully joined the network through {peer_id}"
                        )
                        logger.info(
                            f"Current leader is {self.leader_id} with term {self.term}"
                        )
                        logger.info(f"Network peers: {self.peers}")

                        # Add self to servers info
                        self.servers_info[self.server_id] = replication.ServerInfo(
                            server_id=self.server_id,
                            address=self.address,
                            role="follower",
                        )

                        # Reset election timer
                        self.reset_election_timer()
                        break
            except Exception as e:
                logger.error(f"Failed to join network through {peer_id}: {str(e)}")

        if not joined:
            logger.warning(
                "Failed to join network through any peer. Starting as leader."
            )
            self.become_leader()
