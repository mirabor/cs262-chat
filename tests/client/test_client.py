import unittest
from unittest.mock import patch, MagicMock
from src.client.client import Client

class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()

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
        mock_protocol.deserialize.return_value = {
            "status": "connected",
            "message": "Connected successfully"
        }
        
        # Mock socket receive
        mock_socket_instance.recv.return_value = b'connection response'
        
        # Test connection
        result = self.client.connect()
        
        # Verify results
        self.assertTrue(result)
        mock_socket_instance.connect.assert_called_once()
        mock_socket_instance.send.assert_called_once()

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
        
        # Test connection
        result = self.client.connect()
        
        # Verify results
        self.assertFalse(result)
        mock_socket_instance.connect.assert_called_once()

    @patch("socket.socket")
    def test_send_message(self, mock_socket):
        """Test sending a message."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        self.client.connect()

        self.client.send_message({"action": "test"})
        self.assertEqual(mock_socket_instance.send.call_count, 2)  # One for connect, one for test

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
        mock_protocol.deserialize.side_effect = [
            {"status": "connected"},  # For connect()
            {"message": "test message"}  # For receive_message()
        ]
        
        # Connect and receive message
        self.client.connect()
        message = self.client.receive_message()
        
        # Verify results
        self.assertEqual(message, {"message": "test message"})
        self.assertEqual(mock_socket_instance.recv.call_count, 2)  # Once for connect, once for receive
        # Mock the protocol's deserialize method to return a valid response
        self.client.protocol.deserialize.return_value = {"action": "test"}

        response = self.client.receive_message()
        self.assertEqual(response, {"action": "test"})

    def test_disconnect(self):
        """Test disconnecting from the server."""
        self.client.socket = MagicMock()
        self.client.disconnect()
        self.client.socket.close.assert_called_once()