"""
    Server Program Entry Point
    
This module serves as the entry point for the chat server application.
It parses command line arguments and initializes the appropriate server type.
"""

import argparse
import sys
import os

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.server.tcp_server import TCPServer
from src.server.grpc_server import GRPCServer

def main():
    """Parse command line arguments and start the appropriate server"""
    parser = argparse.ArgumentParser(description='Start the chat server')
    parser.add_argument('--mode', choices=['socket', 'grpc'], default='socket',
                        help='Server mode: socket (default) or grpc')
    parser.add_argument('--host', type=str, required=True,
                        help='Host address for this server (format: host:port)')
    parser.add_argument('--peers', type=str, default='',
                        help='Comma-separated list of peer addresses (format: peer1:port,peer2:port,...)')
    args = parser.parse_args()

    if args.mode == 'grpc':
        server = GRPCServer(host=args.host, peers=args.peers.split(',') if args.peers else [])
    else:
        server = TCPServer()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()