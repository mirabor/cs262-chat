import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.client.logic import ChatAppLogic
from src.protocol.json_protocol import JsonProtocol

class TestChatAppLogic(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock the network client
        self.mock_client = MagicMock()
        self.mock_protocol = JsonProtocol()
        
        # Initialize chat app logic with mocked client
        self.logic = ChatAppLogic(client=self.mock_client)
        
        # Set up common test data
        self.test_user = {
            "username": "testuser",
            "nickname": "Test User",
            "password": "password123",
            "message_limit": 10
        }
        
        # Mock successful responses
        self.mock_success_response = {
            "status": "success",
            "message": "Operation successful"
        }

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.patcher.stop()

    def test_signup_success(self):
        """Test successful user signup with valid credentials."""
        # Mock client response
        self.mock_client.send_request.return_value = self.mock_success_response
        
        result = self.logic.signup("testuser", "Test User", "password123")
        
        # Verify success
        self.assertTrue(result)
        
        # Verify correct request was sent
        self.mock_client.send_request.assert_called_with({
            "operation": "signup",
            "username": "testuser",
            "nickname": "Test User",
            "password": "password123"
        })

    def test_signup_duplicate_user(self):
        """Test signup fails with duplicate username."""
        # Mock failed response for duplicate user
        self.mock_client.send_request.return_value = {
            "status": "error",
            "message": "Username already exists"
        }
        
        result = self.logic.signup("testuser", "Another User", "password456")
        self.assertFalse(result)

    def test_signup_invalid_input(self):
        """Test signup fails with invalid input."""
        result = self.logic.signup("", "", "")
        self.assertFalse(result)

    def test_login_success(self):
        """Test successful login with valid credentials."""
        # Mock successful login response
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Login successful",
            "data": self.test_user
        }
        
        result = self.logic.login("testuser", "password123")
        self.assertTrue(result)
        
        # Verify user data was stored
        self.assertEqual(self.logic.current_user, "testuser")
        self.assertEqual(self.logic.message_limit, 10)

    def test_login_invalid_credentials(self):
        """Test login fails with invalid credentials."""
        self.logic.signup("testuser", "Test User", "password123")
        result = self.logic.login("testuser", "wrongpassword")
        self.assertFalse(result)

    def test_start_chat(self):
        """Test starting a new chat between users."""
        # Mock successful chat creation
        expected_chat_id = "chat123"
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Chat created",
            "data": {
                "chat_id": expected_chat_id,
                "participants": ["user1", "user2"],
                "created_at": datetime.now().isoformat()
            }
        }
        
        chat_id = self.logic.start_chat("user1", "user2")
        
        # Verify chat creation
        self.assertEqual(chat_id, expected_chat_id)
        self.mock_client.send_request.assert_called_with({
            "operation": "create_chat",
            "participants": ["user1", "user2"]
        })

    def test_send_message(self):
        """Test sending a message in a chat."""
        chat_id = "chat123"
        message_content = "Hello!"
        
        # Mock successful message sending
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Message sent",
            "data": {
                "msg_id": "msg123",
                "chat_id": chat_id,
                "sender": "user1",
                "content": message_content,
                "timestamp": datetime.now().isoformat(),
                "status": "sent"
            }
        }
        
        result = self.logic.send_message(chat_id, "user1", message_content)
        
        # Verify message sending
        self.assertTrue(result)
        self.mock_client.send_request.assert_called_with({
            "operation": "send_message",
            "chat_id": chat_id,
            "sender": "user1",
            "content": message_content
        })

    def test_delete_messages(self):
        """Test deleting messages from a chat."""
        chat_id = "chat123"
        message_ids = ["msg1", "msg2"]
        
        # Mock successful message deletion
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Messages deleted"
        }
        
        success, _ = self.logic.delete_messages(chat_id, message_ids, "user1")
        
        # Verify deletion request
        self.assertTrue(success)
        self.mock_client.send_request.assert_called_with({
            "operation": "delete_messages",
            "chat_id": chat_id,
            "message_ids": message_ids,
            "user_id": "user1"
        })

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
        # Mock user list response
        mock_users = [
            {"username": "bob", "nickname": "Bob", "status": "online"},
            {"username": "charlie", "nickname": "Charlie", "status": "offline"},
            {"username": "david", "nickname": "David", "status": "online"}
        ]
        
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Users retrieved",
            "data": mock_users
        }
        
        # Test user listing
        users = self.logic.get_users_to_display("alice", "", 0, 10)
        
        # Verify request
        self.mock_client.send_request.assert_called_with({
            "operation": "get_users",
            "current_user": "alice",
            "search_pattern": "",
            "offset": 0,
            "limit": 10
        })
        
        # Verify response processing
        self.assertEqual(len(users), 3)
        self.assertNotIn("alice", [u["username"] for u in users])

    def test_save_settings(self):
        """Test saving user settings."""
        # Mock successful settings update
        new_limit = 15
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Settings updated",
            "data": {"message_limit": new_limit}
        }
        
        success = self.logic.save_settings("testuser", new_limit)
        
        # Verify settings update
        self.assertTrue(success)
        self.mock_client.send_request.assert_called_with({
            "operation": "update_settings",
            "username": "testuser",
            "message_limit": new_limit
        })
        
        # Verify local update
        self.assertEqual(self.logic.message_limit, new_limit)

    def test_delete_account(self):
        """Test account deletion and its effects on chats."""
        # Mock successful account deletion
        self.mock_client.send_request.return_value = {
            "status": "success",
            "message": "Account deleted"
        }
        
        success = self.logic.delete_account("user1")
        
        # Verify deletion request
        self.assertTrue(success)
        self.mock_client.send_request.assert_called_with({
            "operation": "delete_account",
            "username": "user1"
        })
        
        # Verify local state cleared
        self.assertIsNone(self.logic.current_user)
        self.assertEqual(self.logic.message_limit, 0)


if __name__ == "__main__":
    unittest.main()
