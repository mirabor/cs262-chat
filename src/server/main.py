"""
    Server Program Entry Point

This module serves as the entry point for the chat server application.
It parses command line arguments and initializes the appropriate server type.
"""

import argparse
import logging
import sys
import os

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.server.tcp_server import TCPServer
from src.server.grpc_server import GRPCServer


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """Parse command line arguments and start the appropriate server"""
    parser = argparse.ArgumentParser(description="SAMIRA Chat Server 🔥")
    parser.add_argument(
        "--mode",
        choices=["socket", "grpc"],
        default="socket",
        help="Server mode: socket (default) or grpc",
    )

    # for replicated grpc server
    parser.add_argument("--port", type=int, required=False, help="Port to listen on")
    parser.add_argument(
        "--server_id", type=str, required=False, help="Unique server ID"
    )
    parser.add_argument(
        "--peers", type=str, help="Comma-separated list of peer addresses (host:port)"
    )

    args = parser.parse_args()

    peers_list = None
    if args.peers:
        peers_list = args.peers.split(",")

    if args.mode == "grpc" and args.port and args.server_id:
        logger.info("Starting gRPC server in fault-tolerant mode...")
        server = GRPCServer(args.server_id, args.port, peers_list)
    elif args.mode == "grpc":  # standalone grpc server (legacy/first version)
        logger.info("Starting standalone gRPC server...")
        server = GRPCServer()
    else:
        server = TCPServer()

    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()
