import grpc
import logging
from typing import Dict, List

import src.protocol.grpc.replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc


logger = logging.getLogger(__name__)


class NetworkManager:
    """
    Handles network operations like joining a cluster.
    """

    def __init__(self, state):
        self.state = state
        # References to other managers will be set after creation
        self.election_manager = None

    def set_election_manager(self, election_manager):
        """Set the election manager reference."""
        self.election_manager = election_manager

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
                        break
            except Exception as e:
                logger.error(f"Failed to join network through {peer_id}: {str(e)}")

        if not joined:
            logger.warning(
                "Failed to join network through any peer. Starting as leader."
            )
            if self.election_manager:
                self.election_manager.become_leader()
