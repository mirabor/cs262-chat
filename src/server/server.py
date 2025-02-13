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
    save_settings, start_chat, get_user_message_limit, delete_chats, delete_messages, get_messages, get_other_user_in_chat, send_chat_message, get_users_to_display
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
        if action == "send_message":
            # Store the message
            self.store_message(request.get("client_id"), request.get("message", ""))
            response = {
                "status": "received",
                "message": "Message stored successfully",
            }
        elif action == "signup":
            response = signup(request)
        elif action == "login":
            print("calling login api")
            response = login(request)
        elif action == "delete_user":
            response = delete_user(request.get("username"))
        elif action == "get_chats":
            response = get_chats(request.get("user_id"))
        elif action == "get_all_users":
            response = get_all_users(request.get("exclude_username"))
        elif action == "update_view_limit":
            response = update_view_limit(request.get("username"), request.get("new_limit"))
        elif action == "save_settings":
            response = save_settings(request.get("username"), request.get("message_limit"))
        elif action == "start_chat":
            response = start_chat(request.get("current_user"), request.get("other_user"))
        elif action == "get_user_message_limit":
            response = get_user_message_limit(request.get("username"))
        elif action == "delete_chats":
            response = delete_chats(request.get("chat_ids"))
        elif action == "delete_messages":
            response = delete_messages(request.get("chat_id"), request.get("message_indices"), request.get("current_user"))
        elif action == "get_other_user_in_chat":
            response = get_other_user_in_chat(request.get("chat_id"), request.get("current_user"))
        elif action == "get_messages":
            response = get_messages(request)
        elif action == "send_chat_message":
            response = send_chat_message(request.get("chat_id"), request.get("sender"), request.get("content"))
        elif action == "get_users_to_display":
            response = get_users_to_display(request.get("current_user"), request.get("search_pattern"), request.get("current_page"), request.get("users_per_page"))
        else:
            response = {"success": False, "error_message": "Invalid action"}

        return response

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