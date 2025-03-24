import grpc
from concurrent import futures
from typing import Dict, Any

from protocol.grpc import chat_pb2, chat_pb2_grpc
from protocol.config_manager import ConfigManager
from src.services import api
from src.services.chatservicer import ChatServicer


class GRPCServer:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()

        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), self.server)

    def start(self):
        """Start the gRPC server"""
        try:
            # Use same host/port as socket server for now
            address = f"{self.config.host}:{self.config.port}"
            self.server.add_insecure_port(address)
            self.server.start()
            print(f"gRPC Server started on {address}")
            print(f"Maximum workers: 10")
            self.server.wait_for_termination()
        except Exception as e:
            print(f"Error starting gRPC server: {e}")
            self.server.stop(0)
