import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
)

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.client.ui import ChatAppUI
from src.client.client import Client


if __name__ == "__main__":
        # Get client ID and server address from command line arguments if provided
    client_id = sys.argv[1] if len(sys.argv) > 1 else None
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    print(f"Starting client with ID: {client_id}")

    # Create and start client
    client = Client(server_addr=server_addr, client_id=client_id)
    if client.connect():
        app = QApplication(sys.argv)
        window = ChatAppUI(client)
        window.show()
        sys.exit(app.exec())
