from dataclasses import dataclass
import yaml
import os


@dataclass
class NetworkConfig:
    host: str
    port: int
    protocol: str
    max_clients: int
    buffer_size: int
    messages_dir: str


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
                    "buffer_size": 1024,
                    "messages_dir": "client_messages",
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
            }
        }
        with open(self.config_file, "w") as f:
            yaml.dump(config_data, f)
