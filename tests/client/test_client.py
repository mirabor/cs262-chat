import unittest
from unittest.mock import patch, MagicMock
from src.client.client import Client


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        # Override the protocol so that we can control serialize/deserialize.
        self.client.protocol = MagicMock()

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_connect_failure(self, mock_get_network_info, mock_create_socket):
        """Test connection failure when no socket is created."""
        # Simulate failure: create_client_socket returns None.
        mock_create_socket.return_value = None

        result = self.client.connect()
        self.assertFalse(result)
        mock_get_network_info.assert_called_once()

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_connect_exception_handling(self, mock_get_network_info, mock_create_socket):
        """Test that if send_message raises an exception, connect() returns False."""
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # Force protocol.serialize (used in send_message) to raise an exception.
        self.client.protocol.serialize.side_effect = Exception("Unexpected error")

        result = self.client.connect()
        self.assertFalse(result)
        mock_get_network_info.assert_called_once()

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_connect_success(self, mock_get_network_info, mock_create_socket):
        """Test successful connection to the server."""
        # Setup a mock socket.
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # Configure the protocol:
        # When send_message calls serialize, return a dummy bytes object.
        self.client.protocol.serialize.return_value = b'{"client_id":"%s","message":"connection_request"}' % self.client.client_id.encode()
        # Simulate a valid connection response from the server.
        mock_socket_instance.recv.return_value = b'{"status":"connected","message":"Connected successfully"}'
        self.client.protocol.deserialize.return_value = {"status": "connected", "message": "Connected successfully"}

        result = self.client.connect()
        self.assertTrue(result, "Expected connect() to return True but got False.")
        # Verify that send() was called exactly once during send_message.
        mock_socket_instance.send.assert_called_once()
        mock_get_network_info.assert_called_once()

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_receive_message_basic(self, mock_get_network_info, mock_create_socket):
        """Test that receive_message() returns the correct dict given socket data."""
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # For connect(), the first call to receive_message() should return the connection response.
        # Then the explicit call to receive_message() returns our test message.
        self.client.protocol.deserialize.side_effect = [
            {"status": "connected", "message": "Connected successfully"},  # during connect()
            {"message": "hello"}  # for the actual message reception
        ]
        # Simulate two recv() calls:
        # - The first (ignored) for connection response.
        # - The second returns our message bytes.
        mock_socket_instance.recv.side_effect = [b'ignored', b'{"message":"hello"}']

        # First, connect the client.
        self.client.connect()
        # Now receive a message.
        msg = self.client.receive_message()
        self.assertEqual(msg, {"message": "hello"})
        self.assertTrue(mock_socket_instance.recv.called)
        # We don't check socket.connect here because it isn't called by Client.connect().

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_receive_message_deserialization(self, mock_get_network_info, mock_create_socket):
        """Test message deserialization using receive_message()."""
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # For connect(): first call returns connection response,
        # second call (explicit receive_message()) returns our test message.
        self.client.protocol.deserialize.side_effect = [
            {"status": "connected", "message": "Connected successfully"},
            {"message": "test"}
        ]
        mock_socket_instance.recv.side_effect = [b'ignored', b'{"message":"test"}']

        self.client.connect()
        result = self.client.receive_message()
        self.assertEqual(result, {"message": "test"})
        self.assertTrue(mock_socket_instance.recv.called)
        mock_get_network_info.assert_called()

    def test_disconnect(self):
        """Test disconnecting from the server."""
        self.client.socket = MagicMock()
        self.client.disconnect()
        self.client.socket.close.assert_called_once()

    # ---------- Additional Tests for Coverage ----------

    @patch("src.client.client.ConfigManager.create_client_socket", return_value=None)
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_connect_no_socket(self, mock_get_network_info, mock_create_socket):
        """
        Test the branch:
            if not self.socket:
                print("Failed to create socket.")
                return False
        """
        result = self.client.connect()
        self.assertFalse(result)
        mock_get_network_info.assert_called_once()

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_send_message_exception(self, mock_get_network_info, mock_create_socket):
        """
        Test the exception branch inside send_message().
        """
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # Force protocol.serialize to raise an exception.
        self.client.protocol.serialize.side_effect = Exception("Serialize error")
        self.client.socket = mock_socket_instance
        self.client.send_message({"some": "data"})
        # On exception, send_message sets connected to False.
        self.assertFalse(self.client.connected)

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_receive_message_exception(self, mock_get_network_info, mock_create_socket):
        """
        Test the exception branch in receive_message().
        """
        mock_socket_instance = MagicMock()
        mock_create_socket.return_value = mock_socket_instance

        # Force socket.recv to raise an OSError.
        mock_socket_instance.recv.side_effect = OSError("recv error")
        self.client.socket = mock_socket_instance
        result = self.client.receive_message()
        self.assertEqual(result, {})
        self.assertFalse(self.client.connected)

    @patch("src.client.client.ConfigManager.create_client_socket")
    @patch("src.client.client.ConfigManager.get_network_info")
    def test_connect_exception_print(self, mock_get_network_info, mock_create_socket):
        """Test that an exception in connect() prints 'Connection error' and returns False."""
        with patch("builtins.print") as mock_print:
            mock_create_socket.side_effect = Exception("Connection failed")
            result = self.client.connect()
            mock_print.assert_called_with("Connection error: Connection failed")
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
