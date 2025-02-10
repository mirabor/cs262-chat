import socket
import sys
import time
from ..protocol.config_manager import ConfigManager
from ..protocol.protocol_factory import ProtocolFactory
from .utils import hash_password

class Client:
    def __init__(self, server_addr="localhost", client_id=None):
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.server_addr = server_addr
        self.client_id = client_id or f"client_{int(time.time())}"

        # Get protocol from factory
        self.protocol = ProtocolFactory.get_protocol(self.config.protocol)

        self.socket = None
        self.connected = False

    def connect(self):
        """Connect to the server."""
        try:
            # Get local network information
            self.config_manager.get_network_info()
            
            # Create and connect socket using config manager
            self.socket = self.config_manager.create_client_socket(self.server_addr)
            if not self.socket:
                return False

            # Send client identification
            self.send_message(
                {"client_id": self.client_id, "message": "connection_request"}
            )

            response = self.receive_message()
            if response.get("status") == "connected":
                self.connected = True
                print(response.get("message"))
                return True
            else:
                print(f"Connection failed: {response.get('message')}")
                return False

        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def send_message(self, message_dict):
        """Send a message to the server."""
        try:
            data_bytes = self.protocol.serialize(message_dict)
            self.socket.send(data_bytes)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False

    def receive_message(self):
        """Receive a message from the server."""
        try:
            data_bytes = self.socket.recv(1024)
            return self.protocol.deserialize(data_bytes)
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.connected = False
            return {}

    def login(self, username, password):
        """Send a login request to the server."""
        self.send_message({
            "action": "login",
            "username": username,
            "password": password
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def signup(self, username, nickname, password):
        """Send a signup request to the server."""
        if not username or not nickname or not password:
            return False
        if username in self.users:
            return False
        hashed_password = hash_password(password)
        self.send_message({
            "action": "signup",
            "username": username,
            "nickname": nickname,
            "password": hashed_password
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def delete_account(self, username):
        """Send a request to delete a user account."""
        self.send_message({
            "action": "delete_user",
            "username": username
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def get_chats(self, user_id):
        """Request chat history for a user."""
        self.send_message({
            "action": "get_chats",
            "user_id": user_id
        })
        response = self.receive_message()
        return response.get("chats", []), response.get("error_message", "")

    def get_users(self, search_pattern="", page=1, users_per_page=10):
        """Request a list of users."""
        self.send_message({
            "action": "get_all_users",
            "search_pattern": search_pattern,
            "page": page,
            "users_per_page": users_per_page
        })
        response = self.receive_message()
        return response.get("users", []), response.get("error_message", "")

    def update_view_limit(self, username, new_limit):
        """Send a request to update the message view limit."""
        self.send_message({
            "action": "update_view_limit",
            "username": username,
            "new_limit": new_limit
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def disconnect(self):
        """Disconnect from the server."""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("Disconnected from server")

### new things added from ui.py requirements

    def save_settings(self, username, message_limit):
        """Send a request to update user settings."""
        self.send_message({
            "action": "save_settings",
            "username": username,
            "message_limit": message_limit
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def start_chat(self, current_user, other_user):
        """Send a request to start a new chat."""
        self.send_message({
            "action": "start_chat",
            "current_user": current_user,
            "other_user": other_user
        })
        response = self.receive_message()
        return response.get("chat_id"), response.get("error_message", "")

    def get_user_message_limit(self, username):
        """Request the message limit for a user."""
        self.send_message({
            "action": "get_user_message_limit",
            "username": username
        })
        response = self.receive_message()
        return response.get("message_limit"), response.get("error_message", "")

    def delete_chats(self, chat_ids):
        """Send a request to delete chats."""
        self.send_message({
            "action": "delete_chats",
            "chat_ids": chat_ids
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def delete_messages(self, chat_id, message_indices, current_user):
        """Send a request to delete messages."""
        self.send_message({
            "action": "delete_messages",
            "chat_id": chat_id,
            "message_indices": message_indices,
            "current_user": current_user
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")


if __name__ == "__main__":
     # Get client ID and server address from command line arguments if provided
    client_id = sys.argv[1] if len(sys.argv) > 1 else None
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    print(f"Starting client with ID: {client_id}")

    # Create and start client
    client = Client(server_addr=server_addr, client_id=client_id)
    if client.connect():
        client.start_messaging()