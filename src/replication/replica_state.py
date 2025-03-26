import logging
from typing import Dict, List, Optional, Set

import src.protocol.grpc.replication_pb2 as replication

logger = logging.getLogger(__name__)


class ReplicaState:
    """
    Manages all state-related properties of this replica.
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

        # Initialize voting state
        self.voted_for = None
        self.votes_received: Set[str] = set()
        self.election_timer = None

        # Operation log
        self.operation_log = []
        self.last_operation_id = 0

        # Thread control
        self.is_running = False

        # Add initial peers if provided
        if peers:
            for peer in peers:
                # Assuming peer format is "server_id:address"
                if ":" in peer and peer.count(":") == 2:
                    peer_id, peer_address = peer.split(":", 1)
                    self.peers[peer_id] = peer_address
                else:
                    # Assuming direct address format
                    self.peers[f"peer_{len(self.peers)}"] = peer

        # Initialize own server info
        self.servers_info[self.server_id] = replication.ServerInfo(
            server_id=self.server_id, address=self.address, role="follower"
        )
