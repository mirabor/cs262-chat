import unittest
from unittest.mock import patch
from src.client.logic import ChatAppLogic


class TestChatAppLogic(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the file operations to avoid actual file I/O during tests
        self.patcher = patch("builtins.open", create=True)
        self.mock_open = self.patcher.start()
        # Mock empty data files
        self.mock_open.return_value.__enter__.return_value.read.return_value = "{}"

        self.logic = ChatAppLogic()
        # Clear any existing data
        # self.logic.users = {}
        # self.logic.chats = {}

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.patcher.stop()

    def test_signup_success(self):
        """Test successful user signup with valid credentials."""
        result = self.logic.signup("testuser", "Test User", "password123")
        self.assertTrue(result)
        self.assertIn("testuser", self.logic.users)
        self.assertEqual(self.logic.users["testuser"]["nickname"], "Test User")

    def test_signup_duplicate_user(self):
        """Test signup fails with duplicate username."""
        self.logic.signup("testuser", "Test User", "password123")
        result = self.logic.signup("testuser", "Another User", "password456")
        self.assertFalse(result)

    def test_signup_invalid_input(self):
        """Test signup fails with invalid input."""
        result = self.logic.signup("", "", "")
        self.assertFalse(result)

    def test_login_success(self):
        """Test successful login with valid credentials."""
        self.logic.signup("testuser", "Test User", "password123")
        result = self.logic.login("testuser", "password123")
        self.assertTrue(result)

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        self.logic.signup("testuser", "Test User", "password123")
        result = self.logic.login("testuser", "wrongpassword")
        self.assertFalse(result)

    def test_start_chat(self):
        """Test starting a new chat between users."""
        chat_id = self.logic.start_chat("user1", "user2")
        expected_chat_id = "user1_user2" if "user1" < "user2" else "user2_user1"
        self.assertEqual(chat_id, expected_chat_id)
        self.assertIn(chat_id, self.logic.chats)
        self.assertEqual(self.logic.chats[chat_id]["participants"], ["user1", "user2"])

    def test_send_message(self):
        """Test sending a message in a chat."""
        chat_id = self.logic.start_chat("user1", "user2")
        self.logic.send_message(chat_id, "user1", "Hello!")
        messages = self.logic.chats[chat_id]["messages"]
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["content"], "Hello!")
        self.assertEqual(messages[0]["sender"], "user1")

    def test_delete_messages(self):
        """Test deleting messages from a chat."""
        chat_id = self.logic.start_chat("user1", "user2")
        self.logic.send_message(chat_id, "user1", "Message 1")
        self.logic.send_message(chat_id, "user2", "Message 2")
        self.logic.send_message(chat_id, "user1", "Message 3")

        # Try to delete messages
        success, _ = self.logic.delete_messages(chat_id, [0, 2], "user1")
        self.assertTrue(success)
        self.assertEqual(len(self.logic.chats[chat_id]["messages"]), 1)
        self.assertEqual(
            self.logic.chats[chat_id]["messages"][0]["content"], "Message 2"
        )

    def test_delete_unauthorized_messages(self):
        """Test that users can't delete other users' messages."""
        chat_id = self.logic.start_chat("user1", "user2")
        self.logic.send_message(chat_id, "user2", "Message 1")

        # Try to delete message from another user
        success, message = self.logic.delete_messages(chat_id, [0], "user1")
        self.assertFalse(success)
        self.assertEqual(len(self.logic.chats[chat_id]["messages"]), 1)

    def test_get_users_to_display(self):
        """Test filtering and pagination of user list."""
        # Add test users
        test_users = ["alice", "bob", "charlie", "david"]
        for user in test_users:
            self.logic.signup(user, user.capitalize(), "password")

        # Test without search pattern
        users = self.logic.get_users_to_display("alice", "", 0, 2)
        self.assertEqual(len(users), 2)  # Should return 2 users due to pagination
        self.assertNotIn("alice", users)  # Should not include current user

        # Test with search pattern
        users = self.logic.get_users_to_display("alice", "b", 0, 10)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0], "bob")

    def test_save_settings(self):
        """Test saving user settings."""
        self.logic.signup("testuser", "Test User", "password123")
        self.logic.save_settings("testuser", 10)
        self.assertEqual(self.logic.users["testuser"]["message_limit"], 10)

    def test_delete_account(self):
        """Test account deletion and its effects on chats."""
        # Create users and chat
        self.logic.signup("user1", "User One", "password1")
        self.logic.signup("user2", "User Two", "password2")
        chat_id = self.logic.start_chat("user1", "user2")
        self.logic.send_message(chat_id, "user1", "Hello")

        # Delete account
        self.logic.delete_account("user1")

        # Verify user and their chats are removed
        self.assertNotIn("user1", self.logic.users)
        self.assertNotIn(chat_id, self.logic.chats)


if __name__ == "__main__":
    unittest.main()
