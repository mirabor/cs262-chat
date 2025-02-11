import socket
import json
import sys
import threading
from queue import Queue
from protocol.config_manager import ConfigManager
from protocol.protocol_factory import ProtocolFactory


class ChatClient:
    def __init__(self, server_addr="localhost", client_id=None):
        print("Initializing ChatClient...")  # Debug print
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.server_addr = server_addr
        self.client_id = client_id or f"client_{hash(threading.get_ident())}"

        print(f"Using config: {self.config.__dict__}")  # Debug print
        print(f"Client ID: {self.client_id}")  # Debug print

        self.protocol = ProtocolFactory.get_protocol(self.config.protocol)

        self.socket = None
        self.connected = False
        self.send_queue = Queue()
        self.recv_buffer = b""

    def receive_message(self):
        print("Attempting to receive message...")  # Debug print
        try:
            data = self.socket.recv(1024)
            if data:
                print(f"Received raw data: {data}")  # Debug print
                msg = self.protocol.deserialize(data)
                print(f"Deserialized message: {msg}")  # Debug print
                return msg
            return None
        except Exception as e:
            print(f"Error receiving message: {e}")
            return None

    def connect(self):
        print(f"Connecting to {self.server_addr}:{self.config.port}")
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_addr, self.config.port))
            print("Socket connected")

            # Send initial connection message directly (not through queue)
            connection_msg = {"client_id": self.client_id, "type": "connection_request"}
            print(f"Sending connection message: {connection_msg}")
            data = self.protocol.serialize(connection_msg)
            print(f"Serialized data: {data}")  # Debug print
            self.socket.sendall(data)
            print("Initial message sent")

            # Wait for response
            response = self.receive_message()
            print(f"Got response: {response}")  # Debug print

            if response and response.get("status") == "connected":
                print(f"Connected to server: {response.get('message')}")
                self.connected = True
                self.start_message_handlers()
                return True

            print(
                f"Connection failed: {response.get('message') if response else 'No response'}"
            )
            return False

        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def start_message_handlers(self):
        print("Starting message handlers...")  # Debug print
        self.sender_thread = threading.Thread(target=self.sender_loop)
        self.sender_thread.daemon = True
        self.sender_thread.start()

        self.receiver_thread = threading.Thread(target=self.receiver_loop)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()

    def sender_loop(self):
        print("Sender loop started")  # Debug print
        while self.connected:
            try:
                message = self.send_queue.get()
                if message is None:
                    break
                print(f"Sending message: {message}")  # Debug print
                data = self.protocol.serialize(message)
                self.socket.sendall(data)
            except Exception as e:
                print(f"Error in sender loop: {e}")
                self.connected = False
                break

    def receiver_loop(self):
        print("Receiver loop started")  # Debug print
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    print("Server closed connection")
                    self.connected = False
                    break
                print(f"Received data in loop: {data}")  # Debug print
                self.recv_buffer += data
                self.process_received_data()
            except Exception as e:
                print(f"Error in receiver loop: {e}")
                self.connected = False
                break

    def process_received_data(self):
        try:
            message = self.protocol.deserialize(self.recv_buffer)
            self.recv_buffer = b""
            self.handle_message(message)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Error processing message: {e}")
            self.recv_buffer = b""

    def handle_message(self, message):
        print(f"Handling message: {message}")  # Debug print

    def send_message(self, message):
        print(f"Queueing message: {message}")  # Debug print
        self.send_queue.put(message)

    def start_chat(self):
        if not self.connected:
            print("Not connected to server")
            return

        print("Chat session started. Type 'quit' to exit.")
        try:
            while self.connected:
                msg = input(f"{self.client_id}> ")
                if msg.lower() == "quit":
                    break

                chat_message = {
                    "client_id": self.client_id,
                    "type": "chat_message",
                    "content": msg,
                }
                self.send_message(chat_message)

        except KeyboardInterrupt:
            print("\nChat session ended by user")
        finally:
            self.disconnect()

    def disconnect(self):
        print("Disconnecting...")  # Debug print
        self.connected = False
        if self.socket:
            try:
                self.send_queue.put(None)
                self.socket.close()
            except Exception as e:
                print(f"Error closing socket: {e}")
        print("Disconnected from server")


def main():
    print("Starting chat client...")  # Debug print
    client_id = (
        sys.argv[1] if len(sys.argv) > 1 else f"client_{hash(threading.get_ident())}"
    )
    server_addr = sys.argv[2] if len(sys.argv) > 2 else "localhost"

    client = ChatClient(server_addr=server_addr, client_id=client_id)

    try:
        if client.connect():
            client.start_chat()
    except KeyboardInterrupt:
        print("\nClient terminated by user")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
