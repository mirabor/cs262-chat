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

from src.server.server import Server
from src.server.grpc_server import GRPCServer

def main():
    """Parse command line arguments and start the appropriate server"""
    parser = argparse.ArgumentParser(description='Start the chat server')
    parser.add_argument('--mode', choices=['socket', 'grpc'], default='socket',
                        help='Server mode: socket (default) or grpc')
    args = parser.parse_args()

    if args.mode == 'grpc':
        server = GRPCServer()
    else:
        server = Server()

    try:
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    main()