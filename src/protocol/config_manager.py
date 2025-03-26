from dataclasses import dataclass
import yaml
import os
import socket
import time
from typing import Optional, Tuple


@dataclass
class NetworkConfig:
    host: str
    port: int
    protocol: str
    max_clients: int
    buffer_size: int
    messages_dir: str
    connection_timeout: int = 10
    retry_attempts: int = 3
    retry_delay: int = 2


class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.config_file = "network_config.yaml"
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                config_data = yaml.safe_load(f)
        else:
            # Default configuration
            config_data = {
                "network": {
                    "host": "0.0.0.0",
                    "port": 5555,
                    "protocol": "json",
                    "max_clients": 10,
                    "buffer_size": 2048,
                    "messages_dir": "client_messages",
                    "connection_timeout": 10,
                    "retry_attempts": 3,
                    "retry_delay": 2,
                }
            }
            # Create default config file
            with open(self.config_file, "w") as f:
                yaml.dump(config_data, f)

        self.network = NetworkConfig(**config_data["network"])

    def save_config(self):
        config_data = {
            "network": {
                "host": self.network.host,
                "port": self.network.port,
                "protocol": self.network.protocol,
                "max_clients": self.network.max_clients,
                "buffer_size": self.network.buffer_size,
                "messages_dir": self.network.messages_dir,
                "connection_timeout": self.network.connection_timeout,
                "retry_attempts": self.network.retry_attempts,
                "retry_delay": self.network.retry_delay,
            }
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)

    def resolve_server_address(self, server_addr: str) -> Tuple[str, str]:
        """Resolve server address to IP and return both the original and resolved addresses."""
        try:
            print(f"Attempting to resolve server: {server_addr}")
            server_info = socket.getaddrinfo(
                server_addr, self.network.port, socket.AF_INET, socket.SOCK_STREAM
            )
            if server_info:
                resolved_ip = server_info[0][4][0]
                print(f"Resolved {server_addr} to IP: {resolved_ip}")
                return server_addr, resolved_ip
        except Exception as e:
            print(f"Warning: Could not resolve hostname: {e}")
        return server_addr, server_addr

    def get_network_info(self) -> None:
        """Print network information for the current machine."""
        hostname = socket.gethostname()
        print(f"\nLocal hostname: {hostname}")
        print("Network interfaces:")
        print("-" * 20)
        try:
            interfaces = socket.getaddrinfo(hostname, None)
            for info in interfaces:
                addr = info[4][0]
                self.network.host = addr
                if not addr.startswith("fe80"):  # Skip link-local addresses
                    print(f"Interface: {addr}")
        except Exception as e:
            print(f"Error getting network interfaces: {e}")

    def create_client_socket(self, server_addr: str) -> Optional[socket.socket]:
        """Create and connect a client socket with retry logic."""
        _, resolved_ip = self.resolve_server_address(server_addr)

        for attempt in range(self.network.retry_attempts):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{self.network.retry_attempts}")
                    time.sleep(self.network.retry_delay)

                print(f"Attempting to connect to {resolved_ip}:{self.network.port}...")
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.settimeout(self.network.connection_timeout)
                print("Socket created, attempting connection...")
                client_socket.connect((resolved_ip, self.network.port))
                print("Connection established!")
                return client_socket

            except Exception as e:
                print(f"Connection error: {e}")
                if client_socket:
                    client_socket.close()

        print("Failed to connect after all retry attempts")
        return None
