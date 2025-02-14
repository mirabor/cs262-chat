import socket
import sys
import time

from src.protocol.config_manager import ConfigManager
from src.protocol.protocol_factory import ProtocolFactory

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
        try:
            # Get local network information
            self.config_manager.get_network_info()
            
            # Create and connect socket using config manager
            self.socket = self.config_manager.create_client_socket(self.server_addr)
            if not self.socket:
                print("Failed to create socket.")
                return False

            # Send client identification directly (bypass send_message since we're not connected yet)
            try:
                data_bytes = self.protocol.serialize(
                    {"client_id": self.client_id, "message": "connection_request"}
                )
                self.socket.send(data_bytes)
            except Exception as e:
                print(f"Error sending connection request: {e}")
                return False

            # Receive response directly (bypass receive_message since we're not connected yet)
            try:
                data_bytes = self.socket.recv(2048)
                response = self.protocol.deserialize(data_bytes)
            except Exception as e:
                print(f"Error receiving connection response: {e}")
                return False

            if response.get("status") == "connected":
                self.connected = True
                print(response.get("message"))
                return True
            else:
                print(f"Connection failed: {response.get('message')}")
                if self.socket:
                    self.socket.close()
                return False

        except Exception as e:
            print(f"Connection error: {e}")
            if self.socket:
                self.socket.close()
            return False

    def send_message(self, message_dict):
        """Send message to server"""
        print(f"send_message called with: {message_dict}")
        if not self.socket or not self.connected:
            if not self.reconnect():
                return False
        try:
            data_bytes = self.protocol.serialize(message_dict)
            self.socket.send(data_bytes)
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def receive_message(self):
        """Receive message from server"""
        if not self.socket or not self.connected:
            return {"success": False, "error_message": "Not connected to server"}
        try:
            data_bytes = self.socket.recv(2048)
            return self.protocol.deserialize(data_bytes)
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.connected = False
            if self.socket:
                self.socket.close()
                self.socket = None
            return {"success": False, "error_message": str(e)}

    def reconnect(self):
        """Attempt to reconnect to the server"""
        if self.socket:
            self.socket.close()
        return self.connect()

    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("Disconnected from server")

