import os
import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication,
)

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.client.ui import ChatAppUI
from src.client.client import Client
from src.client.grpc_logic import ChatAppLogicGRPC


def main():
    parser = argparse.ArgumentParser(description="Chat Client")
    parser.add_argument(
        "--mode",
        choices=["socket", "grpc"],
        default="socket",
        help="Communication mode to use: 'socket' or 'grpc' (default: socket)",
    )
    parser.add_argument(
        "--client_id",
        type=str,
        help="Client ID for socket mode (required for socket mode)",
    )
    parser.add_argument(
        "--server_addr",
        type=str,
        default="localhost",
        help="Server address for socket mode (default: localhost)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="gRPC server host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=50051,
        help="gRPC server port (default: 50051)",
    )
    args = parser.parse_args()

    print(f"Starting client with ID: {args.client_id}")

    # Create and start client
    socket_client, rpc_logic = None, None
    if args.mode == "socket":
        print(f"Connecting to server at {args.server_addr} via {args.mode} mode")
        socket_client = Client(server_addr=args.server_addr, client_id=args.client_id)
    elif args.mode == "grpc":
        print(f"Connecting to server at {args.host}:{args.port} via {args.mode} mode")
        rpc_logic = ChatAppLogicGRPC(host=args.host, port=args.port)
    else:
        raise ValueError(f"Invalid mode: {args.mode}")

    # Create and show UI
    app = QApplication(sys.argv)
    window = ChatAppUI(socket_client, rpc_logic)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
