import socket
import threading
import os
from datetime import datetime

from config_manager import ConfigManager
from protocol_factory import ProtocolFactory


class Server:
    def __init__(self):
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()

        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Get protocol from factory
        self.protocol = ProtocolFactory.get_protocol(self.config.protocol)

        # Create messages directory if it doesn't exist
        if not os.path.exists(self.config.messages_dir):
            os.makedirs(self.config.messages_dir)

        # Dictionary to store active clients
        self.active_clients = {}
        self.clients_lock = threading.Lock()

    def start(self):
        """Start the server and listen for connections"""
        try:
            self.server_socket.bind((self.config.host, self.config.port))
            self.server_socket.listen(self.config.max_clients)
            print(f"Server started on {self.config.host}:{self.config.port}")
            print(f"Using protocol: {self.config.protocol}")
            print(f"Maximum clients supported: {self.config.max_clients}")

            while True:
                client_socket, address = self.server_socket.accept()
                if len(self.active_clients) >= self.config.max_clients:
                    response = {
                        "status": "error",
                        "message": "Server at maximum capacity",
                    }
                    client_socket.send(self.protocol.serialize(response))
                    client_socket.close()
                    continue

                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, address):
        """Handle individual client connections"""
        client_id = None
        try:
            # First message should be client identification
            data = client_socket.recv(1024)
            client_data = self.protocol.deserialize(data)
            client_id = client_data.get("client_id")

            if not client_id:
                raise ValueError("No client ID provided")

            # Add client to active clients
            with self.clients_lock:
                self.active_clients[client_id] = client_socket

            print(f"Client {client_id} connected from {address}")

            # Send acknowledgment
            response = {
                "status": "connected",
                "message": f"Successfully connected as {client_id}",
            }
            client_socket.send(self.protocol.serialize(response))

            # Handle client messages
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break

                message_data = self.protocol.deserialize(data)
                self.store_message(client_id, message_data.get("message", ""))

                # Send acknowledgment
                response = {
                    "status": "received",
                    "message": "Message stored successfully",
                }
                client_socket.send(self.protocol.serialize(response))

        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            if client_id:
                with self.clients_lock:
                    self.active_clients.pop(client_id, None)
            client_socket.close()
            print(f"Client {client_id} disconnected")

    def store_message(self, client_id, message):
        """Store client message in their designated file"""
        filename = os.path.join(self.config.messages_dir, f"{client_id}.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(filename, "a") as f:
            f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    # Create and start server
    server = Server()
    server.start()
