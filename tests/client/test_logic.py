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

    @patch('PyQt6.QtWidgets.QMessageBox')
    def test_send_message(self, mock_qmessagebox):
        """Test sending a message in a chat."""
        # Setup test data
        chat_id = "chat123"
        sender = "user1"
        content = "Hello!"
        
        # Setup mock response
        self.mock_client.receive_message.return_value = {
            "success": True,
            "error_message": ""
        }
        
        # Call send_chat_message
        success, error = self.logic.send_chat_message(chat_id, sender, content)
        
        # Verify results
        self.assertTrue(success)
        self.assertEqual(error, "")
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "send_chat_message",
            "chat_id": chat_id,
            "sender": sender,
            "content": content
        })
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

    @patch('PyQt6.QtWidgets.QMessageBox')
    def test_save_settings(self, mock_qmessagebox):
        """Test saving user settings."""
        # Setup test data
        username = "testuser"
        message_limit = 10
        
        # Setup mock response
        self.mock_client.receive_message.return_value = {
            "success": True,
            "error_message": ""
        }
        
        # Call save_settings
        success, error = self.mock_client.save_settings(username, message_limit)
        
        # Verify results
        self.assertTrue(success)
        self.assertEqual(error, "")
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "save_settings",
            "username": username,
            "message_limit": message_limit
        })

    def test_delete_account(self):
        """Test account deletion and its effects on chats."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.delete_account("testuser")
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_signup_invalid_input(self):
        """Test signup fails with invalid input."""
        result, error = self.logic.signup("", "", "")
        self.assertFalse(result)
        self.assertEqual(error, "All fields are required.")

    def test_login_invalid_input(self):
        """Test login fails with invalid input."""
        result, error = self.logic.login("", "")
        self.assertFalse(result)
        self.assertEqual(error, "Username and password are required.")

    def test_save_settings_invalid_limit(self):
        """Test saving settings fails with invalid limit."""
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Invalid limit"}
        result, error = self.logic.save_settings("testuser", 0)
        self.assertFalse(result)
        self.assertEqual(error, "Invalid limit")

    def test_get_unread_message_count(self):
        """Test counting unread messages."""
        # Setup test data
        chat_id = "chat1"
        current_user = "user1"
        
        # Setup mock response for get_chats
        self.mock_client.receive_message.return_value = {
            "success": True,
            "chats": {
                chat_id: {
                    "chat_id": chat_id,
                    "messages": [
                        {"sender": "user2", "content": "Hi", "read": False},
                        {"sender": "user2", "content": "Hello", "read": False},
                        {"sender": "user1", "content": "Hey", "read": True}
                    ]
                }
            },
            "error_message": ""
        }
        
        # Call get_unread_message_count
        count, error = self.logic.get_unread_message_count(chat_id, current_user)
        
        # Verify results
        self.assertEqual(count, 2)  # Two unread messages from user2
        self.assertIsNone(error)
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "get_chats",
            "user_id": current_user
        })

    def test_get_other_user_in_chat(self):
        """Test getting the other user in a chat."""
        self.mock_client.receive_message.return_value = {"user": "user2", "error_message": ""}
        user, error = self.logic.get_other_user_in_chat("chat1", "user1")
        self.assertEqual(user, "user2")
        self.assertEqual(error, "")
    
    def test_signup_invalid_input(self):
        """Test signup fails with invalid input."""
        result, error = self.logic.signup("", "", "")
        self.assertFalse(result)
        self.assertEqual(error, "All fields are required.")

    def test_login_invalid_input(self):
        """Test login fails with invalid input."""
        result, error = self.logic.login("", "")
        self.assertFalse(result)
        self.assertEqual(error, "Username and password are required.")

    def test_save_settings_invalid_limit(self):
        """Test saving settings fails with invalid limit."""
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Invalid limit"}
        result, error = self.logic.save_settings("testuser", 0)
        self.assertFalse(result)
        self.assertEqual(error, "Invalid limit")

    @patch('PyQt6.QtWidgets.QMessageBox')
    def test_send_message(self, mock_qmessagebox):
        """Test sending a message."""
        # Setup test data
        chat_id = "chat123"
        sender = "user1"
        content = "Hello!"
        
        # Setup mock response
        self.mock_client.receive_message.return_value = {
            "success": True,
            "error_message": ""
        }
        
        # Call send_chat_message
        success, error = self.logic.send_chat_message(chat_id, sender, content)
        
        # Verify results
        self.assertTrue(success)
        self.assertEqual(error, "")
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "send_chat_message",
            "chat_id": chat_id,
            "sender": sender,
            "content": content
        })

    @patch('PyQt6.QtWidgets.QMessageBox')
    def test_delete_selected_messages(self, mock_qmessagebox):
        """Test deleting selected messages."""
        # Setup test data
        chat_id = "chat123"
        message_indices = [0, 2]
        current_user = "user1"
        
        # Setup mock response
        self.mock_client.receive_message.return_value = {
            "success": True,
            "error_message": ""
        }
        
        # Call delete_messages
        success, error = self.logic.delete_messages(chat_id, message_indices, current_user)
        
        # Verify results
        self.assertTrue(success)
        self.assertEqual(error, "")
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "delete_messages",
            "chat_id": chat_id,
            "message_indices": message_indices,
            "current_user": current_user
        })

    def test_get_chats(self):
        """Test getting chat list."""
        # Setup test data
        user_id = "user1"
        expected_chats = [
            {"chat_id": "chat1", "messages": []},
            {"chat_id": "chat2", "messages": []}
        ]
        
        # Setup mock response
        self.mock_client.receive_message.return_value = {
            "success": True,
            "chats": {chat["chat_id"]: chat for chat in expected_chats},
            "error_message": ""
        }
        
        # Call get_chats
        chats, error = self.logic.get_chats(user_id)
        
        # Verify results
        self.assertEqual(len(chats), 2)
        self.assertEqual(error, "")
        
        # Verify correct message was sent
        self.mock_client.send_message.assert_called_once_with({
            "action": "get_chats",
            "user_id": user_id
        })

    def test_delete_chats(self):
        """Test deleting chats."""
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        result, error = self.logic.delete_chats(["chat1", "chat2"])
        self.assertTrue(result)
        self.assertEqual(error, "")

    def test_get_unread_message_count(self):
        """Test counting unread messages."""
        self.mock_client.receive_message.return_value = {"chats": {"chat1": {"messages": [{"read": False}]}}}
        count, error = self.logic.get_unread_message_count("chat1", "user1")
        self.assertEqual(count, 1)
        self.assertEqual(error, None)


if __name__ == "__main__":
    unittest.main()