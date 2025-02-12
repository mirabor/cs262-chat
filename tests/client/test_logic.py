import unittest
from unittest.mock import MagicMock
from src.client.logic import ChatAppLogic

class TestChatAppLogic(unittest.TestCase):
    def setUp(self):
        # Create a mock client object
        self.mock_client = MagicMock()
        self.chat_app_logic = ChatAppLogic(self.mock_client)

    def test_delete_chats(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the delete_chats method
        success, error_message = self.chat_app_logic.delete_chats([1, 2, 3])
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_delete_messages(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the delete_messages method
        success, error_message = self.chat_app_logic.delete_messages(1, [0, 1], "user1")
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_login(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the login method
        success, error_message = self.chat_app_logic.login("user1", "password123")
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_signup(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the signup method
        success, error_message = self.chat_app_logic.signup("user1", "nickname1", "password123")
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_save_settings(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the save_settings method
        success, error_message = self.chat_app_logic.save_settings("user1", 100)
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_start_chat(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"chat_id": 1, "error_message": ""}
        
        # Call the start_chat method
        chat_id, error_message = self.chat_app_logic.start_chat("user1", "user2")
        
        # Assert that the method returned the expected values
        self.assertEqual(chat_id, 1)
        self.assertEqual(error_message, "")

    def test_get_users_to_display(self):
        # Mock the client's receive_message method to return a list of users
        self.mock_client.receive_message.return_value = {"users": ["user1", "user2"], "error_message": ""}
        
        # Call the get_users_to_display method
        users, error_message = self.chat_app_logic.get_users_to_display("user1", "*", 1, 10)
        
        # Assert that the method returned the expected values
        self.assertEqual(users, ["user1", "user2"])
        self.assertEqual(error_message, "")

    def test_delete_account(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the delete_account method
        success, error_message = self.chat_app_logic.delete_account("user1")
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_get_user_message_limit(self):
        # Mock the client's receive_message method to return a message limit
        self.mock_client.receive_message.return_value = {"message_limit": 100, "error_message": ""}
        
        # Call the get_user_message_limit method
        message_limit, error_message = self.chat_app_logic.get_user_message_limit("user1")
        
        # Assert that the method returned the expected values
        self.assertEqual(message_limit, 100)
        self.assertEqual(error_message, "")

    def test_get_chats(self):
        # Mock the client's receive_message method to return a list of chats
        self.mock_client.receive_message.return_value = {
            "success": True,
            "chats": {
                "1": {"messages": [], "other_user": "user2"},
                "2": {"messages": [], "other_user": "user3"}
            },
            "error_message": ""
        }
        
        # Call the get_chats method
        chats, error_message = self.chat_app_logic.get_chats("user1")
        
        # Assert that the method returned the expected values
        self.assertEqual(len(chats), 2)
        self.assertEqual(error_message, "")

    def test_get_other_user_in_chat(self):
        # Mock the client's receive_message method to return a user
        self.mock_client.receive_message.return_value = {"user": "user2", "error_message": ""}
        
        # Call the get_other_user_in_chat method
        user, error_message = self.chat_app_logic.get_other_user_in_chat(1, "user1")
        
        # Assert that the method returned the expected values
        self.assertEqual(user, "user2")
        self.assertEqual(error_message, "")

    def test_get_messages(self):
        # Mock the client's receive_message method to return a list of messages
        self.mock_client.receive_message.return_value = {"messages": ["msg1", "msg2"], "error_message": ""}
        
        # Call the get_messages method
        messages, error_message = self.chat_app_logic.get_messages(1)
        
        # Assert that the method returned the expected values
        self.assertEqual(messages, ["msg1", "msg2"])
        self.assertEqual(error_message, "")

    def test_send_chat_message(self):
        # Mock the client's receive_message method to return a success response
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}
        
        # Call the send_chat_message method
        success, error_message = self.chat_app_logic.send_chat_message(1, "user1", "Hello")
        
        # Assert that the method returned the expected values
        self.assertTrue(success)
        self.assertEqual(error_message, "")

    def test_get_unread_message_count(self):
        # Mock the get_chats method to return a list of chats with unread messages
        self.chat_app_logic.get_chats = MagicMock(return_value=([
            {"chat_id": 1, "messages": [{"sender": "user2", "read": False}, {"sender": "user1", "read": True}]}
        ], ""))
        
        # Call the get_unread_message_count method
        unread_count, error_message = self.chat_app_logic.get_unread_message_count(1, "user1")
        
        # Assert that the method returned the expected values
        self.assertEqual(unread_count, 1)
        self.assertEqual(error_message, "")

if __name__ == "__main__":
    unittest.main()