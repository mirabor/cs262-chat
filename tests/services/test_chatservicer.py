"""Test cases for the ChatServicer class."""

import unittest
from unittest.mock import MagicMock, patch

from protocol.grpc import chat_pb2
from src.services.chatservicer import ChatServicer


class TestChatServicer(unittest.TestCase):
    """Test cases for the ChatServicer class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.servicer = ChatServicer()
        self.context = MagicMock()

    @patch('src.services.api.signup')
    def test_signup_success(self, mock_signup):
        """Test successful user signup."""
        # Configure mock
        mock_signup.return_value = {"success": True}

        # Create request
        request = chat_pb2.SignupRequest(
            username="testuser",
            nickname="Test User",
            password="password123"
        )

        # Call the method
        response = self.servicer.Signup(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_signup.assert_called_once_with({
            "username": "testuser",
            "nickname": "Test User",
            "password": "password123"
        })

    @patch('src.services.api.signup')
    def test_signup_failure(self, mock_signup):
        """Test failed user signup."""
        # Configure mock
        mock_signup.return_value = {
            "success": False,
            "error_message": "Username already exists"
        }

        # Create request
        request = chat_pb2.SignupRequest(
            username="existinguser",
            nickname="Existing User",
            password="password123"
        )

        # Call the method
        response = self.servicer.Signup(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "Username already exists")

    @patch('src.services.api.login')
    def test_login_success(self, mock_login):
        """Test successful user login."""
        # Configure mock
        mock_login.return_value = {
            "success": True,
            "user_id": 123,  # int32 in protobuf
            "nickname": "Test User",
            "view_limit": 50
        }

        # Create request
        request = chat_pb2.LoginRequest(
            username="testuser",
            password="password123"
        )

        # Call the method
        response = self.servicer.Login(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.user_id, 123)
        self.assertEqual(response.nickname, "Test User")
        self.assertEqual(response.view_limit, 50)
        self.assertEqual(response.error_message, "")

    @patch('src.services.api.login')
    def test_login_failure(self, mock_login):
        """Test failed user login."""
        # Configure mock
        mock_login.return_value = {
            "success": False,
            "error_message": "Invalid credentials"
        }

        # Create request
        request = chat_pb2.LoginRequest(
            username="testuser",
            password="wrongpassword"
        )

        # Call the method
        response = self.servicer.Login(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "Invalid credentials")

    @patch('src.services.api.delete_user')
    def test_delete_user(self, mock_delete_user):
        """Test deleting a user."""
        # Configure mock
        mock_delete_user.return_value = {}

        # Create request
        request = chat_pb2.DeleteUserRequest(username="testuser")

        # Call the method
        response = self.servicer.DeleteUser(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_delete_user.assert_called_once_with("testuser")

    @patch('src.services.api.delete_user')
    def test_delete_user_failure(self, mock_delete_user):
        """Test failed user deletion."""
        # Configure mock
        mock_delete_user.return_value = {"error_message": "User not found"}

        # Create request
        request = chat_pb2.DeleteUserRequest(username="nonexistentuser")

        # Call the method
        response = self.servicer.DeleteUser(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "User not found")

    @patch('src.services.api.get_user_message_limit')
    def test_get_user_message_limit(self, mock_get_limit):
        """Test getting user message limit."""
        # Configure mock
        mock_get_limit.return_value = {"message_limit": "50"}

        # Create request
        request = chat_pb2.GetUserMessageLimitRequest(username="testuser")

        # Call the method
        response = self.servicer.GetUserMessageLimit(request, self.context)

        # Verify the response
        self.assertEqual(response.limit, "50")
        self.assertEqual(response.error_message, "")

    @patch('src.services.api.save_settings')
    def test_save_settings(self, mock_save_settings):
        """Test saving user settings."""
        # Configure mock
        mock_save_settings.return_value = {}

        # Create request
        request = chat_pb2.SaveSettingsRequest(
            username="testuser",
            message_limit="100"
        )

        # Call the method
        response = self.servicer.SaveSettings(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_save_settings.assert_called_once_with("testuser", "100")

    @patch('src.services.api.save_settings')
    def test_save_settings_failure(self, mock_save_settings):
        """Test saving user settings with failure."""
        # Configure mock
        mock_save_settings.return_value = {"error_message": "User not found"}

        # Create request
        request = chat_pb2.SaveSettingsRequest(
            username="nonexistentuser",
            message_limit="100"
        )

        # Call the method
        response = self.servicer.SaveSettings(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "User not found")

    @patch('src.services.api.get_users_to_display')
    def test_get_users_to_display(self, mock_get_users):
        """Test getting users to display."""
        # Configure mock
        mock_get_users.return_value = {
            "users": ["user1", "user2", "user3"],
            "total_pages": 2
        }

        # Create request
        request = chat_pb2.GetUsersToDisplayRequest(
            exclude_username="currentuser",
            search_pattern="user",
            current_page=1,
            users_per_page=10
        )

        # Call the method
        response = self.servicer.GetUsersToDisplay(request, self.context)

        # Verify the response
        self.assertEqual(response.usernames, ["user1", "user2", "user3"])
        self.assertEqual(response.total_pages, 2)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_get_users.assert_called_once_with(
            "currentuser", "user", 1, 10
        )

    @patch('src.services.api.get_users_to_display')
    def test_get_users_to_display_error(self, mock_get_users):
        """Test getting users to display with error."""
        # Configure mock
        mock_get_users.return_value = {
            "error_message": "Database error"
        }

        # Create request
        request = chat_pb2.GetUsersToDisplayRequest(
            exclude_username="currentuser",
            search_pattern="user",
            current_page=1,
            users_per_page=10
        )

        # Call the method
        response = self.servicer.GetUsersToDisplay(request, self.context)

        # Verify the response
        self.assertEqual(response.error_message, "Database error")

    @patch('src.services.api.get_chats')
    def test_get_chats(self, mock_get_chats):
        """Test getting chats for a user."""
        # Configure mock
        mock_get_chats.return_value = {
            "chats": [
                {"chat_id": "chat1", "other_user": "user1", "unread_count": 5},
                {"chat_id": "chat2", "other_user": "user2", "unread_count": 0}
            ]
        }

        # Create request
        request = chat_pb2.GetChatsRequest(user_id="testuser")

        # Call the method
        response = self.servicer.GetChats(request, self.context)

        # Verify the response
        self.assertEqual(len(response.chats), 2)
        self.assertEqual(response.chats[0].chat_id, "chat1")
        self.assertEqual(response.chats[0].other_user, "user1")
        self.assertEqual(response.chats[0].unread_count, 5)
        self.assertEqual(response.chats[1].chat_id, "chat2")
        self.assertEqual(response.chats[1].other_user, "user2")
        self.assertEqual(response.chats[1].unread_count, 0)
        self.assertEqual(response.error_message, "")

    @patch('src.services.api.get_chats')
    def test_get_chats_error(self, mock_get_chats):
        """Test getting chats with error."""
        # Configure mock
        mock_get_chats.return_value = {
            "error_message": "User not found"
        }

        # Create request
        request = chat_pb2.GetChatsRequest(user_id="nonexistentuser")

        # Call the method
        response = self.servicer.GetChats(request, self.context)

        # Verify the response
        self.assertEqual(response.error_message, "User not found")
        self.assertEqual(len(response.chats), 0)

    @patch('src.services.api.start_chat')
    def test_start_chat_success(self, mock_start_chat):
        """Test starting a chat successfully."""
        # Configure mock
        mock_start_chat.return_value = {
            "success": True,
            "chat_id": "newchat123"
        }

        # Create request
        request = chat_pb2.StartChatRequest(
            current_user="testuser",
            other_user="otheruser"
        )

        # Call the method
        response = self.servicer.StartChat(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.chat.chat_id, "newchat123")

        # Verify the API call
        mock_start_chat.assert_called_once_with("testuser", "otheruser")

    @patch('src.services.api.start_chat')
    def test_start_chat_failure(self, mock_start_chat):
        """Test starting a chat with failure."""
        # Configure mock
        mock_start_chat.return_value = {
            "success": False,
            "error_message": "User not found"
        }

        # Create request
        request = chat_pb2.StartChatRequest(
            current_user="testuser",
            other_user="nonexistentuser"
        )

        # Call the method
        response = self.servicer.StartChat(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "User not found")

    @patch('src.services.api.get_messages')
    def test_get_messages(self, mock_get_messages):
        """Test getting messages for a chat."""
        # Configure mock
        mock_get_messages.return_value = {
            "messages": [
                {
                    "sender": "user1",
                    "content": "Hello",
                    "timestamp": "2023-01-01 12:00:00"
                },
                {
                    "sender": "user2",
                    "content": "Hi there",
                    "timestamp": "2023-01-01 12:01:00"
                }
            ]
        }

        # Create request
        request = chat_pb2.GetMessagesRequest(
            chat_id="chat123",
            current_user="testuser"
        )

        # Call the method
        response = self.servicer.GetMessages(request, self.context)

        # Verify the response
        self.assertEqual(len(response.messages), 2)
        self.assertEqual(response.messages[0].sender, "user1")
        self.assertEqual(response.messages[0].content, "Hello")
        self.assertEqual(response.messages[0].timestamp, "2023-01-01 12:00:00")
        self.assertEqual(response.messages[1].sender, "user2")
        self.assertEqual(response.messages[1].content, "Hi there")
        self.assertEqual(response.messages[1].timestamp, "2023-01-01 12:01:00")
        self.assertEqual(response.error_message, "")

    @patch('src.services.api.get_messages')
    def test_get_messages_error(self, mock_get_messages):
        """Test getting messages with error."""
        # Configure mock
        mock_get_messages.return_value = {
            "error_message": "Chat not found"
        }

        # Create request
        request = chat_pb2.GetMessagesRequest(
            chat_id="nonexistentchat",
            current_user="testuser"
        )

        # Call the method
        response = self.servicer.GetMessages(request, self.context)

        # Verify the response
        self.assertEqual(response.error_message, "Chat not found")
        self.assertEqual(len(response.messages), 0)

    @patch('src.services.api.send_chat_message')
    def test_send_chat_message_success(self, mock_send_message):
        """Test sending a chat message successfully."""
        # Configure mock
        mock_send_message.return_value = {"success": True}

        # Create request
        request = chat_pb2.SendMessageRequest(
            chat_id="chat123",
            sender="testuser",
            content="Hello, world!"
        )

        # Call the method
        response = self.servicer.SendChatMessage(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_send_message.assert_called_once_with(
            "chat123", "testuser", "Hello, world!"
        )

    @patch('src.services.api.send_chat_message')
    def test_send_chat_message_failure(self, mock_send_message):
        """Test sending a chat message with failure."""
        # Configure mock
        mock_send_message.return_value = {
            "success": False,
            "error_message": "Chat not found"
        }

        # Create request
        request = chat_pb2.SendMessageRequest(
            chat_id="nonexistentchat",
            sender="testuser",
            content="Hello, world!"
        )

        # Call the method
        response = self.servicer.SendChatMessage(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "Chat not found")

    @patch('src.services.api.delete_messages')
    def test_delete_messages(self, mock_delete_messages):
        """Test deleting messages."""
        # Configure mock
        mock_delete_messages.return_value = {}

        # Create request
        request = chat_pb2.DeleteMessagesRequest(
            chat_id="chat123",
            message_indices=[1, 2, 3],
            current_user="testuser"
        )

        # Call the method
        response = self.servicer.DeleteMessages(request, self.context)

        # Verify the response
        self.assertTrue(response.success)
        self.assertEqual(response.error_message, "")

        # Verify the API call
        mock_delete_messages.assert_called_once_with(
            "chat123", [1, 2, 3], "testuser"
        )

    @patch('src.services.api.delete_messages')
    def test_delete_messages_failure(self, mock_delete_messages):
        """Test deleting messages with failure."""
        # Configure mock
        mock_delete_messages.return_value = {
            "error_message": "Chat not found"
        }

        # Create request
        request = chat_pb2.DeleteMessagesRequest(
            chat_id="nonexistentchat",
            message_indices=[1, 2, 3],
            current_user="testuser"
        )

        # Call the method
        response = self.servicer.DeleteMessages(request, self.context)

        # Verify the response
        self.assertFalse(response.success)
        self.assertEqual(response.error_message, "Chat not found")


if __name__ == "__main__":
    unittest.main()
