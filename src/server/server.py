import selectors
import socket
import types
from protocol.config_manager import ConfigManager
from protocol.protocol_factory import ProtocolFactory


class Server:
    def __init__(self):
        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.network
        self.config_manager.get_network_info()

        # Initialize selector
        self.sel = selectors.DefaultSelector()

        # Initialize server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Get protocol from factory
        self.protocol = ProtocolFactory.get_protocol(self.config.protocol)

        # Dictionary to store active clients
        self.active_clients = {}

    def start(self):
        """Start the server and listen for connections"""
        try:
            self.server_socket.bind((self.config.host, self.config.port))
            self.server_socket.listen(self.config.max_clients)
            self.server_socket.setblocking(False)

            # Register server socket for accepting connections
            self.sel.register(self.server_socket, selectors.EVENT_READ, data=None)

            print(f"Server started on {self.config.host}:{self.config.port}")
            print(f"Using protocol: {self.config.protocol}")

            while True:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        # Server socket event - new connection
                        self.accept_connection(key.fileobj)
                    else:
                        # Client socket event - handle data
                        self.handle_client_event(key, mask)

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.sel.close()
            self.server_socket.close()

    def accept_connection(self, sock):
        """Handle new client connections"""
        client_socket, addr = sock.accept()
        client_socket.setblocking(False)

        if len(self.active_clients) >= self.config.max_clients:
            response = {
                "status": "error",
                "message": "Server at maximum capacity",
            }
            client_socket.send(self.protocol.serialize(response))
            client_socket.close()
            return

        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", client_id=None)

        # Register client socket for read and write events
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.sel.register(client_socket, events, data=data)
        print(f"Accepted connection from {addr}")

    def handle_client_event(self, key, mask):
        """Handle client socket events"""
        sock = key.fileobj
        data = key.data

        try:
            if mask & selectors.EVENT_READ:
                print(f"Read event for {data.addr}")  # Debug print
                recv_data = sock.recv(1024)
                if recv_data:
                    print(f"Received raw data: {recv_data}")  # Debug print
                    data.inb += recv_data
                    print(f"Current buffer: {data.inb}")  # Debug print
                    self.process_messages(sock, data)
                else:
                    print(f"No data received from {data.addr}")
                    self.close_connection(sock, data)

            if mask & selectors.EVENT_WRITE:
                if data.outb:
                    print(f"Writing data: {data.outb}")  # Debug print
                    sent = sock.send(data.outb)
                    data.outb = data.outb[sent:]

        except Exception as e:
            print(f"Error in handle_client_event: {e}")
            self.close_connection(sock, data)

    def process_messages(self, sock, data):
        """Process received messages from buffer"""
        try:
            msg = self.protocol.deserialize(data.inb)
            print(f"Processing message: {msg}")  # Debug print

            # Handle initial connection message
            if not data.client_id and msg.get("type") == "connection_request":
                client_id = msg.get("client_id")
                if client_id:
                    data.client_id = client_id
                    self.active_clients[client_id] = sock
                    print(f"Client {client_id} connected")

                    response = {
                        "status": "connected",
                        "message": f"Successfully connected as {client_id}",
                    }
                    data.outb += self.protocol.serialize(response)

            # Handle other messages
            elif data.client_id:
                response = {"status": "received", "message": "Message processed"}
                data.outb += self.protocol.serialize(response)

            # Clear input buffer after processing
            data.inb = b""

        except json.JSONDecodeError:
            print("Incomplete message, waiting for more data")
            # Don't clear buffer - wait for more data
        except Exception as e:
            print(f"Error processing message: {e}")
            data.inb = b""

    def close_connection(self, sock, data):
        """Clean up client connection"""
        print(f"Closing connection to {data.addr}")
        if data.client_id:
            self.active_clients.pop(data.client_id, None)
        self.sel.unregister(sock)
        sock.close()


if __name__ == "__main__":
    server = Server()
    server.start()
