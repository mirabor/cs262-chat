import grpc
import logging
import time
from typing import Dict

import src.protocol.grpc.replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc

from .config import (
    HEARTBEAT_INTERVAL,
    MAX_MISSED_HEARTBEATS,
)

logger = logging.getLogger(__name__)


class HeartbeatManager:
    """
    Manages heartbeat sending and checking for this replica
    """

    def __init__(self, state):
        self.state = state
        # Reference to the election manager will be set after creation
        self.election_manager = None

    def set_election_manager(self, election_manager):
        """Set the election manager reference."""
        self.election_manager = election_manager

    def heartbeat_loop(self):
        """Continuously send heartbeats if leader, or check leader liveness if follower."""
        last_heartbeat_time = {}
        connection_failure_count = {}  # Track consecutive failures

        while self.state.is_running:
            try:
                if self.state.role == "leader":
                    self._send_heartbeats_as_leader(
                        last_heartbeat_time, connection_failure_count
                    )
                elif self.state.role == "follower" and self.state.leader_id:
                    self._check_leader_liveness(
                        last_heartbeat_time, connection_failure_count
                    )

                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {str(e)}")
                time.sleep(1)  # Avoid tight loops in case of persistent errors

    def _send_heartbeats_as_leader(self, last_heartbeat_time, connection_failure_count):
        """Send heartbeats to all followers if this node is the leader."""
        peers_to_remove = []

        for peer_id, peer_address in self.state.peers.items():
            try:
                with grpc.insecure_channel(peer_address) as channel:
                    stub = replication_grpc.ReplicationServiceStub(channel)

                    request = replication.HeartbeatRequest(
                        server_id=self.state.server_id,
                        term=self.state.term,
                        role="leader",
                        timestamp=int(time.time()),
                    )

                    response = stub.Heartbeat(request, timeout=1)

                    if response.term > self.state.term:
                        # Higher term discovered, revert to follower
                        self.state.term = response.term
                        self.state.role = "follower"
                        self.state.leader_id = None
                        if self.election_manager:
                            self.election_manager.reset_election_timer()
                        logger.info(
                            f"Discovered higher term {response.term}, reverting to follower"
                        )
                        break

                    # Update server info
                    self.state.servers_info[peer_id] = replication.ServerInfo(
                        server_id=peer_id,
                        address=peer_address,
                        role=response.role,
                    )

                    # Reset failure count on successful connection
                    connection_failure_count[peer_id] = 0
                    last_heartbeat_time[peer_id] = time.time()
            except Exception as e:
                # Increment failure count
                connection_failure_count[peer_id] = (
                    connection_failure_count.get(peer_id, 0) + 1
                )

                # Only log the first few failures to reduce noise
                if connection_failure_count[peer_id] <= 5:
                    logger.warning(
                        f"Failed to send heartbeat to {peer_id} at {peer_address}: {str(e)}"
                    )
                elif (
                    connection_failure_count[peer_id] % 30 == 0
                ):  # Log periodically after that
                    logger.warning(
                        f"Still unable to reach {peer_id} after {connection_failure_count[peer_id]} attempts"
                    )

                # Check if peer has been unresponsive for too long
                if peer_id in last_heartbeat_time:
                    if (
                        time.time() - last_heartbeat_time[peer_id]
                        > MAX_MISSED_HEARTBEATS * HEARTBEAT_INTERVAL
                    ):
                        # Mark for removal (don't remove during iteration)
                        peers_to_remove.append(peer_id)
                elif connection_failure_count[peer_id] >= MAX_MISSED_HEARTBEATS:
                    # If we've never had a successful connection, remove after several attempts
                    peers_to_remove.append(peer_id)

        # Remove unresponsive peers outside the loop
        for peer_id in peers_to_remove:
            if peer_id in self.state.peers:
                logger.warning(
                    f"Peer {peer_id} has been unresponsive, removing from peers"
                )
                del self.state.peers[peer_id]
                if peer_id in self.state.servers_info:
                    del self.state.servers_info[peer_id]
                if peer_id in last_heartbeat_time:
                    del last_heartbeat_time[peer_id]
                if peer_id in connection_failure_count:
                    del connection_failure_count[peer_id]

    def _check_leader_liveness(self, last_heartbeat_time, connection_failure_count):
        """Check if the current leader is still alive."""
        if self.state.leader_id in self.state.peers:
            leader_address = self.state.peers[self.state.leader_id]

            # If we haven't heard from the leader for too long
            leader_timeout = False

            if self.state.leader_id in last_heartbeat_time:
                if (
                    time.time() - last_heartbeat_time[self.state.leader_id]
                    > MAX_MISSED_HEARTBEATS * HEARTBEAT_INTERVAL
                ):
                    logger.warning(
                        f"Leader {self.state.leader_id} has been unresponsive"
                    )
                    leader_timeout = True

            # If we've had too many connection failures
            if (
                self.state.leader_id in connection_failure_count
                and connection_failure_count[self.state.leader_id]
                >= MAX_MISSED_HEARTBEATS
            ):
                logger.warning(f"Leader {self.state.leader_id} has been unreachable")
                leader_timeout = True

            if leader_timeout:
                # Reset leader info
                self.state.leader_id = None
                # Reset the election timer to prepare for election
                if self.election_manager:
                    self.election_manager.reset_election_timer()

    def check_leader_status(self):
        """Check if the current leader is still available."""
        if (
            self.state.role == "follower"
            and self.state.leader_id
            and self.state.leader_id in self.state.peers
        ):
            leader_address = self.state.peers[self.state.leader_id]
            logger.debug(
                f"Checking status of leader {self.state.leader_id} at {leader_address}"
            )

            try:
                with grpc.insecure_channel(leader_address) as channel:
                    stub = replication_grpc.ReplicationServiceStub(channel)

                    request = replication.HeartbeatRequest(
                        server_id=self.state.server_id,
                        term=self.state.term,
                        role="follower",
                        timestamp=int(time.time()),
                    )

                    # Short timeout to quickly detect failures
                    response = stub.Heartbeat(request, timeout=1)
                    return True  # Leader is responsive
            except Exception as e:
                logger.warning(
                    f"Leader {self.state.leader_id} appears to be down: {str(e)}"
                )
                if self.election_manager:
                    self.election_manager.start_election()
                return False
        return None  # Not a follower or no leader to check
