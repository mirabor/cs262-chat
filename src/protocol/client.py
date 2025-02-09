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
            print(f"Attempting to connect to {self.host}:{self.port}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10 second timeout
            print(f"Socket created, attempting connection...")
            self.socket.connect((self.host, self.port))
            print("Connection established!")

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
    # Get client ID and server address from command line arguments if provided
    client_id = sys.argv[1] if len(sys.argv) > 1 else None
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    print(f"Starting client with ID: {client_id}")
    
    # Show client network information
    hostname = socket.gethostname()
    print(f"\nClient hostname: {hostname}")
    print("Client network interfaces:")
    print("-" * 20)
    interfaces = socket.getaddrinfo(hostname, None)
    for info in interfaces:
        addr = info[4][0]
        if not addr.startswith('fe80'):  # Skip link-local addresses
            print(f"Interface: {addr}")
    
    print(f"\nAttempting to resolve and connect to server: {server_addr}")
    
    try:
        # Try to resolve the hostname to IP
        import socket
        server_info = socket.getaddrinfo(server_addr, 5555, socket.AF_INET, socket.SOCK_STREAM)
        if server_info:
            server_ip = server_info[0][4][0]  # Get the first resolved IP
            print(f"Resolved {server_addr} to IP: {server_ip}")
        else:
            server_ip = server_addr
    except Exception as e:
        print(f"Warning: Could not resolve hostname: {e}")
        server_ip = server_addr

    # Create and start client
    client = Client(host=server_ip, client_id=client_id)
    if client.connect():
        client.start_messaging()
