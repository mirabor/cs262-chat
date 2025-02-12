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
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_get_protocol.return_value = MagicMock()

        # Mock the protocol's deserialize method to return a valid response
        mock_get_protocol.return_value.deserialize.return_value = {
            "status": "connected",
            "message": "Connected",
        }

        self.assertTrue(self.client.connect())
        mock_socket_instance.send.assert_called_once()

    @patch("socket.socket")
    def test_connect_failure(self, mock_socket):
        """Test connection failure."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.recv.return_value = b'{"status": "failed", "message": "Connection failed"}'

        self.assertFalse(self.client.connect())

    @patch("socket.socket")
    def test_send_message(self, mock_socket):
        """Test sending a message."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        self.client.connect()

        self.client.send_message({"action": "test"})
        self.assertEqual(mock_socket_instance.send.call_count, 2)  # One for connect, one for test

    @patch("socket.socket")
    def test_receive_message(self, mock_socket):
        """Test receiving a message."""
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        self.client.connect()

        # Mock the protocol's deserialize method to return a valid response
        self.client.protocol.deserialize.return_value = {"action": "test"}

        response = self.client.receive_message()
        self.assertEqual(response, {"action": "test"})

    def test_disconnect(self):
        """Test disconnecting from the server."""
        self.client.socket = MagicMock()
        self.client.disconnect()
        self.client.socket.close.assert_called_once()