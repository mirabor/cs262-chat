# note: this is missing deleting messages, updating settings (6 message limit), and account management

import unittest
from unittest.mock import patch, mock_open, MagicMock
import json
from PyQt6.QtWidgets import QApplication
import sys
from simple_chat import ChatApp

class TestChatApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.window = ChatApp()
        self.window.users = {}
        self.window.chats = {}
        self.window.current_user = 'test_user'
        self.window.users['test_user'] = {"password": "password", "nickname": "Test", "message_limit": 6}

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    def test_load_data_creates_files_if_not_exist(self, mock_file):
        self.window.load_data()
        self.assertEqual(self.window.users, {})
        self.assertEqual(self.window.chats, {})

    @patch("builtins.open", new_callable=mock_open)
    def test_save_data(self, mock_file):
        self.window.users['new_user'] = {"password": "1234", "nickname": "Newbie", "message_limit": 6}
        self.window.save_data()
        mock_file.assert_called_with("users.json", "w")
        handle = mock_file()
        handle.write.assert_called_once_with(json.dumps(self.window.users))

    def test_signup_success(self):
        with patch.object(self.window, 'save_data') as mock_save, \
             patch('PyQt6.QtWidgets.QMessageBox.information') as mock_msg:
            self.window.signup('new_user', 'Newbie', '1234')
            self.assertIn('new_user', self.window.users)
            mock_save.assert_called_once()
            mock_msg.assert_called_once_with(self.window, "Success", "Account created successfully")

    def test_signup_existing_user(self):
        self.window.users['existing_user'] = {"password": "pass", "nickname": "ExUser", "message_limit": 6}
        with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_msg:
            self.window.signup('existing_user', 'ExUser', 'pass')
            mock_msg.assert_called_once_with(self.window, "Error", "Username already taken")

    def test_login_success(self):
        with patch.object(self.window, 'show_home_page') as mock_home:
            self.window.login('test_user', 'password')
            self.assertEqual(self.window.current_user, 'test_user')
            mock_home.assert_called_once()

    def test_login_failure(self):
        with patch('PyQt6.QtWidgets.QMessageBox.critical') as mock_msg:
            self.window.login('test_user', 'wrongpassword')
            mock_msg.assert_called_once_with(self.window, "Error", "Invalid username or password")

    def test_send_message(self):
        chat_id = 'test_user_other_user'
        self.window.chats[chat_id] = {"participants": ["test_user", "other_user"], "messages": []}
        with patch.object(self.window, 'save_data') as mock_save:
            self.window.send_message(chat_id, "Hello!")
            self.assertEqual(len(self.window.chats[chat_id]['messages']), 1)
            self.assertEqual(self.window.chats[chat_id]['messages'][0]['content'], "Hello!")
            mock_save.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

if __name__ == "__main__":
    unittest.main()