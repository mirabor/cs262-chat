import unittest
from unittest.mock import patch, MagicMock
from src.client.client import Client

class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    @patch("socket.socket")
    @patch("src.protocol.protocol_factory.ProtocolFactory.get_protocol")
    def test_connect_failure(self, mock_get_protocol, mock_socket):
        """Test connection failure."""
        # Setup mock socket with connection error
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.connect.side_effect = ConnectionRefusedError()
        
        # Setup mock protocol
        mock_protocol = MagicMock()
        mock_get_protocol.return_value = mock_protocol
        
        # Mock protocol deserialization to return a valid response
        mock_protocol.deserialize.return_value = {"status": "connected"}
        
        # Test connection
        with patch.object(self.client, 'send_message', return_value=None):
            with patch.object(self.client, 'receive_message', return_value=None):
                result = self.client.connect()
        
        # Verify results
        self.assertFalse(result)
        mock_socket_instance.connect.assert_called_once()

    @patch("socket.socket")
    @patch("src.protocol.protocol_factory.ProtocolFactory.get_protocol")
    def test_connect_success(self, mock_get_protocol, mock_socket):
        """Test successful connection to the server."""
        # Setup mock socket
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Setup mock protocol
        mock_protocol = MagicMock()
        mock_get_protocol.return_value = mock_protocol
        
        # Mock protocol serialization/deserialization
        mock_protocol.serialize.return_value = b'connection request'
        mock_protocol.deserialize.return_value = {"status": "connected", "message": "Connected successfully"}
        
        # Test connection
        with patch.object(self.client, 'send_message', return_value=None):
            with patch.object(self.client, 'receive_message', return_value={"status": "connected", "message": "Connected successfully"}):
                result = self.client.connect()
        
        # Verify results
        self.assertTrue(result)
        mock_socket_instance.connect.assert_called_once()
        mock_socket_instance.send.assert_called_once()

    @patch("socket.socket")
    @patch("src.protocol.protocol_factory.ProtocolFactory.get_protocol")
    def test_receive_message(self, mock_get_protocol, mock_socket):
        """Test receiving a message."""
        # Setup mock socket
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Setup mock protocol
        mock_protocol = MagicMock()
        mock_get_protocol.return_value = mock_protocol
        
        # Mock successful connection
        mock_protocol.deserialize.return_value = {"message": "test message"}
        
        # Connect and receive message
        with patch.object(self.client, 'connect', return_value=True):
            message = self.client.receive_message()
        
        # Verify results
        self.assertEqual(message, {"message": "test message"})
        mock_socket_instance.recv.assert_called_once()

    def test_disconnect(self):
        """Test disconnecting from the server."""
        self.client.socket = MagicMock()
        self.client.disconnect()
        self.client.socket.close.assert_called_once()