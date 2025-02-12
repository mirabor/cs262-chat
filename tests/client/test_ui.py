import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication, QLabel
import sys
import os
from src.client.ui import ChatAppUI
from src.client.components import ChatWidget, MessageWidget
from PyQt6.QtWidgets import QMessageBox

# Set Qt to use minimal platform plugin to avoid opening windows during tests
os.environ["QT_QPA_PLATFORM"] = "minimal"

# Create QApplication instance for testing
if not QApplication.instance():
    app = QApplication([])

class TestChatAppUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all test methods."""
        # Ensure we have a QApplication instance
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock ChatAppLogic to avoid actual file operations
        self.mock_client = MagicMock()
        self.ui = ChatAppUI(self.mock_client)

    def test_login_success(self):
        """Test successful login updates UI state."""
        # Configure mock
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}

        # Mock UI elements
        with patch("PyQt6.QtWidgets.QLineEdit") as mock_line_edit:
            mock_username = MagicMock()
            mock_username.text.return_value = "testuser"
            mock_password = MagicMock()
            mock_password.text.return_value = "password123"

            self.ui.username_input = mock_username
            self.ui.password_input = mock_password

            # Mock QMessageBox and other UI elements
            with patch("PyQt6.QtWidgets.QMessageBox.critical"), patch(
                "PyQt6.QtWidgets.QStackedWidget"
            ), patch("PyQt6.QtWidgets.QVBoxLayout"):
                # Perform login
                self.ui.login("testuser", "password123")

                # Verify UI state
                self.assertEqual(self.ui.current_user, "testuser")

    def test_login_failure(self):
        """Test failed login keeps UI in login state."""
        # Configure mock
        self.mock_client.receive_message.return_value = {"success": False, "error_message": "Invalid credentials"}

        # Store initial state
        initial_user = self.ui.current_user

        # Mock UI elements
        with patch("PyQt6.QtWidgets.QLineEdit"), patch(
            "PyQt6.QtWidgets.QMessageBox.critical"
        ):
            # Perform login
            self.ui.login("testuser", "wrongpassword")

            # Verify UI state hasn't changed
            self.assertEqual(self.ui.current_user, initial_user)

    def test_signup_success(self):
        """Test successful signup transitions to login page."""
        # Configure mock
        self.mock_client.receive_message.return_value = {"success": True, "error_message": ""}

        # Mock UI elements
        with patch("PyQt6.QtWidgets.QLineEdit") as mock_line_edit:
            mock_username = MagicMock()
            mock_username.text.return_value = "newuser"
            mock_nickname = MagicMock()
            mock_nickname.text.return_value = "New User"
            mock_password = MagicMock()
            mock_password.text.return_value = "password123"

            self.ui.username_input = mock_username
            self.ui.nickname_input = mock_nickname
            self.ui.password_input = mock_password

            # Mock QMessageBox and other UI elements
            with patch("PyQt6.QtWidgets.QMessageBox.information"), patch(
                "PyQt6.QtWidgets.QMessageBox.critical"
            ), patch("PyQt6.QtWidgets.QStackedWidget"), patch(
                "PyQt6.QtWidgets.QVBoxLayout"
            ):
                # Perform signup
                self.ui.signup("newuser", "New User", "password123")

                # Verify logic call
                self.mock_client.send_message.assert_called_once()

    def test_save_settings(self):
        """Test saving user settings."""
        # Set current user
        self.ui.current_user = "testuser"

        # Mock UI elements
        with patch("PyQt6.QtWidgets.QLineEdit") as mock_line_edit:
            mock_limit = MagicMock()
            mock_limit.text.return_value = "10"

            self.ui.limit_input = mock_limit

            # Mock UI updates
            with patch("PyQt6.QtWidgets.QMessageBox.information"), patch(
                "PyQt6.QtWidgets.QMessageBox.critical"
            ), patch("PyQt6.QtWidgets.QStackedWidget"), patch(
                "PyQt6.QtWidgets.QVBoxLayout"
            ), patch.object(
                self.ui, "show_home_page"
            ):
                # Save settings
                self.ui.save_settings("10")

                # Verify logic call
                self.mock_client.send_message.assert_called_once()


class TestChatWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all test methods."""
        # Ensure we have a QApplication instance
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_chat_widget_display(self):
        """Test chat widget displays correct information."""
        username = "testuser"
        unread_count = 5

        # Mock Qt widgets
        with patch("PyQt6.QtWidgets.QWidget"), patch(
            "PyQt6.QtWidgets.QHBoxLayout"
        ), patch("PyQt6.QtWidgets.QLabel") as mock_label:
            # Create a mock label instance that will be returned when QLabel is called
            mock_label_instance = MagicMock()
            mock_label_instance.text.return_value = username
            mock_label.return_value = mock_label_instance

            # Create another mock label for unread count
            mock_unread_label = MagicMock()
            mock_unread_label.text.return_value = f"[{unread_count} unreads]"

            # Set up the mock to return different instances for different calls
            mock_label.side_effect = [mock_label_instance, mock_unread_label]

            widget = ChatWidget(username, unread_count)

            # Verify widget properties
            labels = widget.findChildren(QLabel)
            self.assertEqual(len(labels), 2)
            self.assertEqual(labels[0].text(), username)
            self.assertEqual(labels[1].text(), f"[{unread_count} unreads]")

class TestMessageWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all test methods."""
        # Ensure we have a QApplication instance
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_message_widget_sender(self):
        """Test message widget displays correctly for sender."""
        message = {"sender": "testuser", "content": "Hello"}

        # Mock Qt widgets
        with patch("PyQt6.QtWidgets.QWidget"), patch(
            "PyQt6.QtWidgets.QVBoxLayout"
        ), patch("PyQt6.QtWidgets.QLabel") as mock_label, patch(
            "PyQt6.QtWidgets.QCheckBox"
        ):
            # Create a mock label instance
            mock_label_instance = MagicMock()
            mock_label_instance.text.return_value = message["content"]
            mock_label.return_value = mock_label_instance

            widget = MessageWidget(message["content"], "testuser")

            # Verify widget properties
            self.assertEqual(widget.findChild(QLabel).text(), "Hello")

    def test_message_widget_receiver(self):
        """Test message widget displays correctly for receiver."""
        message = {"sender": "other", "content": "Hi"}

        # Mock Qt widgets
        with patch("PyQt6.QtWidgets.QWidget"), patch(
            "PyQt6.QtWidgets.QVBoxLayout"
        ), patch("PyQt6.QtWidgets.QLabel") as mock_label, patch(
            "PyQt6.QtWidgets.QCheckBox"
        ):
            # Create a mock label instance
            mock_label_instance = MagicMock()
            mock_label_instance.text.return_value = message["content"]
            mock_label.return_value = mock_label_instance

            widget = MessageWidget(message["content"], "testuser")

            # Verify widget properties
            self.assertEqual(widget.findChild(QLabel).text(), "Hi")


if __name__ == "__main__":
    unittest.main()