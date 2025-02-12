import unittest
from unittest.mock import patch, MagicMock
from src.client.logic import ChatAppLogic

class TestChatAppLogic(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the client to avoid actual network calls
        self.mock_client = MagicMock()
        self.logic = ChatAppLogic(self.mock_client)

    def test_signup_success(self):
        """Test successful user signup with valid credentials."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.signup("testuser", "Test User", "password123")
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_signup_duplicate_user(self):
        """Test signup fails with duplicate username."""
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Username already exists"}
        result, error = self.logic.signup("testuser", "Test User", "password123")
        self.assertFalse(result)
        self.assertEqual(error, "Username already exists")

    def test_login_success(self):
        """Test successful login with valid credentials."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.login("testuser", "password123")
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Invalid credentials"}
        result, error = self.logic.login("testuser", "wrongpassword")
        self.assertFalse(result)
        self.assertEqual(error, "Invalid credentials")

    def test_start_chat(self):
        """Test starting a new chat between users."""
        self.mock_client.receive_message.return_value = {"chat_id": "user1_user2", "error_message": ""}
        chat_id, error = self.logic.start_chat("user1", "user2")
        self.assertEqual(chat_id, "user1_user2")
        self.assertEqual(error, "")

    def test_send_message(self):
        """Test sending a message in a chat."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.send_chat_message("chat_id", "user1", "Hello!")
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_delete_messages(self):
        """Test deleting messages from a chat."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.delete_messages("chat_id", [0, 1], "user1")
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_delete_unauthorized_messages(self):
        """Test that users can't delete other users' messages."""
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Unauthorized"}
        result, error = self.logic.delete_messages("chat_id", [0], "user1")
        self.assertFalse(result)
        self.assertEqual(error, "Unauthorized")

    def test_get_users_to_display(self):
        """Test filtering and pagination of user list."""
        self.mock_client.receive_message.return_value = {"users": ["bob", "charlie"], "error_message": ""}
        users, error = self.logic.get_users_to_display("alice", "b", 0, 10)
        self.assertEqual(users, ["bob", "charlie"])
        self.assertEqual(error, "")

    def test_save_settings(self):
        """Test saving user settings."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.save_settings("testuser", 10)
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_delete_account(self):
        """Test account deletion and its effects on chats."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.delete_account("testuser")
        self.assertTrue(result)
        self.assertEqual(error, "")

if __name__ == "__main__":
    unittest.main()