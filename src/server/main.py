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
    parser = argparse.ArgumentParser(description='Start the chat server')
    parser.add_argument('--mode', choices=['socket', 'grpc'], default='socket',
                        help='Server mode: socket (default) or grpc')
    parser.add_argument('--host', type=str, default='localhost',
                        help='Host address for the server')
    parser.add_argument('--port', type=int, default=5555,
                        help='Port number for the server')
    parser.add_argument('--peers', type=str, default='',
                        help='Comma-separated list of peer addresses')
    args = parser.parse_args()

    peer_addresses = args.peers.split(',') if args.peers else []

    if args.mode == 'grpc':
        server = GRPCServer(host=args.host, port=args.port, peers=peer_addresses)
    else:
        server = TCPServer()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()