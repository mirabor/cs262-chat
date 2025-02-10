import socket
import sys
import time

from protocol.config_manager import ConfigManager
from protocol.protocol_factory import ProtocolFactory


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
        """Send message to server"""
        try:
            data_bytes = self.protocol.serialize(message_dict)
            self.socket.send(data_bytes)
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False

    def receive_message(self):
        """Receive message from server"""
        try:
            data_bytes = self.socket.recv(1024)
            return self.protocol.deserialize(data_bytes)
        except Exception as e:
            print(f"Error receiving message: {e}")
            self.connected = False
            return {}

    def start_messaging(self):
        """Start messaging loop"""
        if not self.connected:
            print("Not connected to server")
            return

        print("Start typing messages (type 'quit' to exit):")
        try:
            while True:
                message = input(f"{self.client_id}> ")
                if message.lower() == "quit":
                    break

                self.send_message({"client_id": self.client_id, "message": message})

                response = self.receive_message()
                if response.get("status") == "received":
                    print("Message delivered")
                else:
                    print(f"Message delivery failed: {response.get('message')}")

        except Exception as e:
            print(f"Error in messaging: {e}")
        finally:
            self.disconnect()

    def disconnect(self):
        """Disconnect from server"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("Disconnected from server")


if __name__ == "__main__":
    # Get client ID and server address from command line arguments if provided
    client_id = sys.argv[1] if len(sys.argv) > 1 else None
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    print(f"Starting client with ID: {client_id}")

    # Create and start client
    client = Client(server_addr=server_addr, client_id=client_id)
    if client.connect():
        client.start_messaging()
