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
