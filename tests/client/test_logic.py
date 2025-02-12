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
        self.mock_client.receive_message.return_value = {
            "chats": {
                "chat1": {
                    "messages": [
                        {"sender": "user2", "read": False},  # Unread message
                        {"sender": "user1", "read": True},   # Read message
                    ]
                }
            }
        }
        count, error = self.logic.get_unread_message_count("chat1", "user1")
        self.assertEqual(count, 1)
        self.assertEqual(error, None)

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

    def test_send_message(self):
        """Test sending a message."""
        with patch.object(self.chat_page.main_window.logic, "send_chat_message") as mock_send:
            mock_send.return_value = (True, "")
            self.chat_page.message_input.setText("Hello")
            self.chat_page._send_chat_message()

            mock_send.assert_called_once_with("chat1", self.mock_parent.current_user, "Hello")

    def test_delete_selected_messages(self):
        """Test deleting selected messages."""
        with patch("PyQt6.QtWidgets.QMessageBox.question") as mock_question:
            mock_question.return_value = MagicMock(return_value=QMessageBox.StandardButton.Yes)

            with patch.object(self.chat_page.main_window.logic, "delete_messages") as mock_delete:
                mock_delete.return_value = (True, "")
                self.chat_page._delete_selected_messages()

                mock_delete.assert_called_once()

    def test_display_chats(self):
        """Test displaying chats."""
        with patch.object(self.home_page.main_window.logic, "get_chats") as mock_get_chats:
            mock_get_chats.return_value = ([{"chat_id": "chat1", "messages": []}], "")
            self.home_page._display_chats()

            self.assertEqual(len(self.home_page.chat_widgets), 1)
    
    def test_save_settings(self):
        """Test saving settings."""
        with patch.object(self.settings_page.main_window.logic, "save_settings") as mock_save:
            mock_save.return_value = (True, "")
            self.settings_page.limit_input.setText("10")
            self.settings_page._handle_save()

            mock_save.assert_called_once_with(self.settings_page.main_window.current_user, 10)
    
    def test_signup(self):
        """Test signup."""
        with patch.object(self.signup_page.main_window, "signup") as mock_signup:
            self.signup_page.username_input.setText("user1")
            self.signup_page.nickname_input.setText("User One")
            self.signup_page.password_input.setText("password123")
            self.signup_page._handle_signup()

            mock_signup.assert_called_once_with("user1", "User One", "password123")

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