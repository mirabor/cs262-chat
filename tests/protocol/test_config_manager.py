import pytest
import os
import socket
import yaml
from src.protocol.config_manager import ConfigManager, NetworkConfig

@pytest.fixture
def config_manager():
    manager = ConfigManager()
    # Save original config file path
    original_config = manager.config_file
    # Use a test config file
    manager.config_file = "test_network_config.yaml"
    yield manager
    # Cleanup after tests
    if os.path.exists(manager.config_file):
        os.remove(manager.config_file)
    manager.config_file = original_config

def test_singleton_instance():
    """Test that ConfigManager is a singleton."""
    manager1 = ConfigManager()
    manager2 = ConfigManager()
    assert manager1 is manager2

def test_default_config_creation(config_manager):
    """Test that default configuration is created when no file exists."""
    if os.path.exists(config_manager.config_file):
        os.remove(config_manager.config_file)
    
    config_manager.load_config()
    
    assert os.path.exists(config_manager.config_file)
    assert isinstance(config_manager.network, NetworkConfig)
    assert config_manager.network.host == "0.0.0.0"
    assert config_manager.network.port == 5555

def test_save_and_load_config(config_manager):
    """Test saving and loading configuration."""
    # Modify some settings
    config_manager.network.port = 6666
    config_manager.network.max_clients = 20
    
    # Save the config
    config_manager.save_config()
    
    # Force reload the config
    config_manager.load_config()
    
    assert config_manager.network.port == 6666
    assert config_manager.network.max_clients == 20

def test_resolve_server_address(config_manager, monkeypatch):
    """Test server address resolution."""
    def mock_getaddrinfo(*args, **kwargs):
        return [(None, None, None, None, ('192.168.1.1', 0))]
    
    monkeypatch.setattr(socket, 'getaddrinfo', mock_getaddrinfo)
    
    original, resolved = config_manager.resolve_server_address('example.com')
    assert original == 'example.com'
    assert resolved == '192.168.1.1'

def test_resolve_server_address_failure(config_manager, monkeypatch):
    """Test server address resolution failure."""
    def mock_getaddrinfo(*args, **kwargs):
        raise socket.gaierror()
    
    monkeypatch.setattr(socket, 'getaddrinfo', mock_getaddrinfo)
    
    original, resolved = config_manager.resolve_server_address('invalid.example')
    assert original == 'invalid.example'
    assert resolved == 'invalid.example'

def test_get_network_info(config_manager, capsys):
    """Test network information retrieval."""
    config_manager.get_network_info()
    captured = capsys.readouterr()
    assert "Local hostname:" in captured.out
    assert "Network interfaces:" in captured.out

def test_create_client_socket_success(config_manager, monkeypatch):
    """Test successful client socket creation."""
    class MockSocket:
        def __init__(self, *args, **kwargs):
            pass
        def settimeout(self, timeout):
            pass
        def connect(self, addr):
            pass
        def close(self):
            pass
    
    monkeypatch.setattr(socket, 'socket', MockSocket)
    
    client_socket = config_manager.create_client_socket('localhost')
    assert client_socket is not None

def test_create_client_socket_failure(config_manager, monkeypatch):
    """Test failed client socket creation."""
    class MockSocket:
        def __init__(self, *args, **kwargs):
            pass
        def settimeout(self, timeout):
            pass
        def connect(self, addr):
            raise ConnectionRefusedError()
        def close(self):
            pass
    
    monkeypatch.setattr(socket, 'socket', MockSocket)
    
    client_socket = config_manager.create_client_socket('localhost')
    assert client_socket is None
