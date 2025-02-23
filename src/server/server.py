import socket
import threading
import os
from datetime import datetime
import sys

from protocol.config_manager import ConfigManager
from protocol.protocol_factory import ProtocolFactory

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, parent_dir)

from src.server.api import (
    signup, login, delete_user, get_chats, get_all_users, update_view_limit,
    save_settings, start_chat, get_user_message_limit, delete_chats, delete_messages, get_messages, send_chat_message, get_users_to_display
)


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
            data = client_socket.recv(2048)
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
                data = client_socket.recv(2048)
                if not data:
                    break

                # Deserialize the incoming data
                request = self.protocol.deserialize(data)

                # Handle the request and get the response
                response = self.handle_request(request)

                # Send the response back to the client
                client_socket.send(self.protocol.serialize(response))

        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
        finally:
            if client_id:
                with self.clients_lock:
                    self.active_clients.pop(client_id, None)
            client_socket.close()
            print(f"Client {client_id} disconnected")

    def handle_request(self, request):
            """Handle incoming requests and return a response"""
            action = request.get("action")
            print(f"Action: {action}")

            actions = {
                "signup": lambda: signup(request),
                "login": lambda: login(request),
                "delete_user": lambda: delete_user(request.get("username")),
                "get_chats": lambda: get_chats(request.get("user_id")),
                "get_all_users": lambda: get_all_users(request.get("exclude_username")),
                "update_view_limit": lambda: update_view_limit(request.get("username"), request.get("new_limit")),
                "save_settings": lambda: save_settings(request.get("username"), request.get("message_limit")),
                "start_chat": lambda: start_chat(request.get("current_user"), request.get("other_user")),
                "get_user_message_limit": lambda: get_user_message_limit(request.get("username")),
                "delete_chats": lambda: delete_chats(request.get("chat_ids")),
                "delete_messages": lambda: delete_messages(request.get("chat_id"), request.get("message_indices"), request.get("current_user")),
                "get_messages": lambda: get_messages(request),
                "send_chat_message": lambda: send_chat_message(request.get("chat_id"), request.get("sender"), request.get("content")),
                "get_users_to_display": lambda: get_users_to_display(request.get("current_user"), request.get("search_pattern"), request.get("current_page"), request.get("users_per_page")),
            }

            handler = actions.get(action, lambda: {"success": False, "error_message": "Invalid action"})
            return handler()


if __name__ == "__main__":
    # Create and start server
    server = Server()
    server.start()