import json
import threading
from json_protocol.server import JsonServer
from json_protocol.client import JsonClient

class TestJsonProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the JSON server in a separate thread for testing."""
        cls.server = JsonServer(host='localhost', port=5001)
        cls.server_thread = threading.Thread(target=cls.server.start)
        cls.server_thread.daemon = True  # Ensure the thread exits when the main program exits
        cls.server_thread.start()

    def test_create_account(self):
        """Test creating a new account."""
        client = JsonClient('localhost', 5001)
        response = client.send_request({
            "operation": "create_account",
            "username": "alice",
            "password": "pass123"
        })
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['message'], 'Account created')