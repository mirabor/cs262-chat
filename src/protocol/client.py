import socket
import json
import sys
import threading
import time


class Client:
    def __init__(self, host="localhost", port=5555, client_id=None):
        self.host = host
        self.port = port
        self.client_id = client_id or f"client_{int(time.time())}"
        self.socket = None
        self.connected = False

    def connect(self):
        """Establish connection with server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            # Send client identification
            self.send_message(
                {"client_id": self.client_id, "message": "connection_request"}
            )

            # Receive connection confirmation
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
            self.socket.send(json.dumps(message_dict).encode())
        except Exception as e:
            print(f"Error sending message: {e}")
            self.connected = False

    def receive_message(self):
        """Receive message from server"""
        try:
            data = self.socket.recv(1024).decode()
            return json.loads(data)
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
    # Get client ID from command line argument if provided
    client_id = sys.argv[1] if len(sys.argv) > 1 else None

    # Create and start client
    client = Client(client_id=client_id)
    if client.connect():
        client.start_messaging()
