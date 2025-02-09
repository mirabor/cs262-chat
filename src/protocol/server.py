import socket
import threading
import json
import os
from datetime import datetime


class Server:
    def __init__(self, host="0.0.0.0", port=5555, max_clients=10):
        self.host = host
        self.port = port
        self.max_clients = max_clients
        self.messages_dir = "client_messages"

        # Create messages directory if it doesn't exist
        if not os.path.exists(self.messages_dir):
            os.makedirs(self.messages_dir)

        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Dictionary to store active clients
        self.active_clients = {}
        self.clients_lock = threading.Lock()

    def start(self):
        """Start the server and listen for connections"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            print(f"Server started on {self.host}:{self.port}")
            print(f"Maximum clients supported: {self.max_clients}")
            
            # Print all available interfaces
            import socket
            hostname = socket.gethostname()
            print(f"\nServer hostname: {hostname}")
            print("\nAvailable interfaces:")
            print("-" * 20)
            interfaces = socket.getaddrinfo(hostname, None)
            for info in interfaces:
                addr = info[4][0]
                if not addr.startswith('fe80'): # Skip link-local addresses
                    print(f"Interface: {addr}")

            while True:
                client_socket, address = self.server_socket.accept()
                if len(self.active_clients) >= self.max_clients:
                    response = {
                        "status": "error",
                        "message": "Server at maximum capacity",
                    }
                    client_socket.send(json.dumps(response).encode())
                    client_socket.close()
                    continue

                # Start a new thread for the client
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
            data = client_socket.recv(1024).decode()
            client_data = json.loads(data)
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
            client_socket.send(json.dumps(response).encode())

            # Handle client messages
            while True:
                data = client_socket.recv(1024).decode()
                if not data:
                    break

                message_data = json.loads(data)
                self.store_message(client_id, message_data.get("message", ""))

                # Send acknowledgment
                response = {
                    "status": "received",
                    "message": "Message stored successfully",
                }
                client_socket.send(json.dumps(response).encode())

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
        filename = os.path.join(self.messages_dir, f"{client_id}.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(filename, "a") as f:
            f.write(f"[{timestamp}] {message}\n")


if __name__ == "__main__":
    # Create and start server
    server = Server(max_clients=10)
    server.start()
