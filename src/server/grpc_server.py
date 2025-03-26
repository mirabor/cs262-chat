import grpc
import logging
from concurrent import futures

from protocol.grpc import chat_pb2_grpc
from protocol.grpc import replication_pb2_grpc
from protocol.config_manager import ConfigManager
from src.services.chatservicer import ChatServicer
from src.services.replication_servicer import ReplicationServicer
from src.replication.replica_node import ReplicaNode


logger = logging.getLogger(__name__)


class GRPCServer:
    def __init__(self, server_id: str = "", port: int = -1, peers: list = None):
        """
        Initialize the gRPC server with the provided server ID, port, and list of peers.

        To make the server fault-tolerant, provide a server ID and list of peers;
        we make these parameters optional to allow for a standalone gRPC server
        (without fault tolerance) and to avoid breaking existing tests.

        """
        self.server_id = server_id if server_id else "grpc-server"
        self.peers = peers if peers else []

        # Initialize the configuration manager that reads from config file
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()

        # Sets the address and port appropriately (priority to provided config)
        self.port = port if port > 0 else self.config.port
        self.address = f"{self.config.host}:{self.port}"

        # Initialize this replica Node
        self.replica = ReplicaNode(self.server_id, self.address, self.peers)
        self.chat_servicer = ChatServicer(self.replica)
        self.replication_servicer = ReplicationServicer(self.replica)

        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_pb2_grpc.add_ChatServiceServicer_to_server(self.chat_servicer, self.server)
        replication_pb2_grpc.add_ReplicationServiceServicer_to_server(
            self.replication_servicer, self.server
        )

    def start(self):
        """Start the gRPC server"""
        try:
            self.server.add_insecure_port(self.address)
            self.server.start()

            logger.info("Server %s started at %s", self.server_id, self.address)
            logger.info("Initial peers: %s", self.replica.peers)

            # Start background tasks for the replica node
            self.replica.start()

            self.server.wait_for_termination()
        except Exception as e:
            logger.error("Error starting gRPC server: %s", e)
            self.shutdown()

    def shutdown(self):
        """Shutdown the server and cleanup resources."""
        self.server.stop(0)
        logger.info("Server %s shutdown", self.server_id)
