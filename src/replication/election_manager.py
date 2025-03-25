import grpc
import logging
import random
import threading
import time
from typing import Set

import src.protocol.grpc.replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc

from .config import (
    ELECTION_TIMEOUT_MIN,
    ELECTION_TIMEOUT_MAX,
)

logger = logging.getLogger(__name__)


class ElectionManager:
    """
    Manages all election-related functionality for this replica.
    """

    def __init__(self, state):
        self.state = state
        # a set to track peers that are down/crashed.
        self.state.down_peers = set()

    def reset_election_timer(self):
        """Reset the election timeout with a random duration."""
        if self.state.election_timer:
            self.state.election_timer.cancel()

        timeout = random.uniform(ELECTION_TIMEOUT_MIN, ELECTION_TIMEOUT_MAX)
        self.state.election_timer = threading.Timer(timeout, self.start_election)
        self.state.election_timer.daemon = True
        self.state.election_timer.start()
        logger.debug(f"Election timer reset with timeout: {timeout:.2f}s")

    def cancel_election_timer(self):
        """Cancel the election timer."""
        if self.state.election_timer:
            self.state.election_timer.cancel()
            self.state.election_timer = None

    def start_election(self):
        """Start a leader election."""
        if self.state.role == "leader":
            self.reset_election_timer()
            return

        # Increment term and vote for self
        self.state.term += 1
        self.state.role = "candidate"
        self.state.voted_for = self.state.server_id
        self.state.votes_received = {self.state.server_id}

        logger.info(
            f"Starting election for term {self.state.term}. {self.state.server_id} votes for itself."
        )

        # Track unique addresses to avoid duplicate requests
        contacted_addresses = set()

        # Request votes from all peers that aren't marked as down
        for peer_id, peer_address in self.state.peers.items():
            if peer_id in self.state.down_peers:
                logger.debug(f"Skipping down peer {peer_id}")
                continue

            # Skip duplicate addresses
            if peer_address in contacted_addresses:
                logger.debug(
                    f"Skipping duplicate address {peer_address} for peer {peer_id}"
                )
                continue

            contacted_addresses.add(peer_address)
            threading.Thread(
                target=self.request_vote, args=(peer_id, peer_address)
            ).start()

        # Reset the election timer for next round if needed
        self.reset_election_timer()

    def request_vote(self, peer_id: str, peer_address: str):
        """Request a vote from a peer."""
        try:
            with grpc.insecure_channel(peer_address) as channel:
                stub = replication_grpc.ReplicationServiceStub(channel)

                # Using heartbeat for vote request (simplified protocol)
                request = replication.HeartbeatRequest(
                    server_id=self.state.server_id,
                    term=self.state.term,
                    role="candidate",
                    timestamp=int(time.time()),
                )

                response = stub.Heartbeat(request, timeout=2)

                # If peer was marked as down but responds now, remove from down_peers
                if peer_id in self.state.down_peers:
                    self.state.down_peers.remove(peer_id)
                    logger.info(f"Peer {peer_id} is back online")

                if response.success and response.term == self.state.term:
                    self.state.votes_received.add(peer_id)
                    logger.info(
                        f"Received vote from {peer_id} for term {self.state.term}"
                    )

                    # Check if we have majority
                    # Count only active peers for majority calculation
                    active_peers_count = len(self.state.peers) - len(
                        self.state.down_peers
                    )
                    if len(self.state.votes_received) > (active_peers_count + 1) / 2:
                        self.become_leader()
                elif response.term > self.state.term:
                    # Higher term discovered, revert to follower
                    self.state.term = response.term
                    self.state.role = "follower"
                    self.state.voted_for = None
                    self.reset_election_timer()
                    logger.info(
                        f"Discovered higher term {response.term}, reverting to follower"
                    )
        except grpc.RpcError as e:
            # Check the status code to determine if the peer is down
            status_code = e.code()
            if status_code == grpc.StatusCode.UNAVAILABLE:
                logger.warning(
                    f"Peer {peer_id} at {peer_address} appears to be down: {str(e)}. Marking as down."
                )
                # Add to down_peers set instead of removing from peers dictionary
                self.state.down_peers.add(peer_id)
            else:
                logger.error(f"Error requesting vote from {peer_id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error requesting vote from {peer_id}: {str(e)}")

    def become_leader(self):
        """Become the leader for the current term."""
        if self.state.role == "leader":
            return

        self.state.role = "leader"
        self.state.leader_id = self.state.server_id
        self.cancel_election_timer()

        # Update server info
        if self.state.server_id in self.state.servers_info:
            self.state.servers_info[self.state.server_id].role = "leader"
        else:
            self.state.servers_info[self.state.server_id] = replication.ServerInfo(
                server_id=self.state.server_id,
                address=self.state.address,
                role="leader",
            )

        logger.info(
            f"🚀 {self.state.server_id} became leader for term {self.state.term}"
        )

        # Notify all peers of the new leader
        for peer_id, peer_address in self.state.peers.items():
            # Skip peers that are known to be down
            if peer_id in self.state.down_peers:
                logger.debug(f"Skipping down peer {peer_id} for leader notification")
                continue

            try:
                with grpc.insecure_channel(peer_address) as channel:
                    stub = replication_grpc.ReplicationServiceStub(channel)

                    request = replication.HeartbeatRequest(
                        server_id=self.state.server_id,
                        term=self.state.term,
                        role="leader",
                        timestamp=int(time.time()),
                    )

                    stub.Heartbeat(request)
            except Exception as e:
                logger.error(f"Error notifying peer {peer_id} of new leader: {str(e)}")
