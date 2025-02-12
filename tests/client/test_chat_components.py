"""Test cases for chat UI components."""

import unittest
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication
import sys
import os
from src.client.components import ChatWidget, MessageWidget, UserListWidget
from datetime import datetime

# Set Qt to use minimal platform plugin to avoid opening windows during tests
os.environ["QT_QPA_PLATFORM"] = "minimal"

class TestChatComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all test methods."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_chat_data = {
            "chat_id": "chat123",
            "participants": ["user1", "user2"],
            "last_message": "Hello!",
            "timestamp": datetime.now().isoformat(),
            "unread_count": 2
        }
        
        self.mock_message_data = {
            "msg_id": "msg123",
            "sender": "user1",
            "content": "Test message",
            "timestamp": datetime.now().isoformat(),
            "status": "delivered"
        }

    def test_chat_widget_creation(self):
        """Test chat widget initialization and display."""
        widget = ChatWidget(self.mock_chat_data)
        
        # Check if widget displays correct information
        assert widget.chat_id == self.mock_chat_data["chat_id"]
        assert str(self.mock_chat_data["unread_count"]) in widget.unread_label.text()
        assert self.mock_chat_data["last_message"] in widget.last_message_label.text()

    def test_chat_widget_click(self):
        """Test chat widget click handling."""
        widget = ChatWidget(self.mock_chat_data)
        
        # Mock click handler
        mock_handler = MagicMock()
        widget.clicked.connect(mock_handler)
        
        # Simulate click
        widget.mousePressEvent(None)
        mock_handler.assert_called_once_with(self.mock_chat_data["chat_id"])

    def test_message_widget_sender_view(self):
        """Test message widget display for sender."""
        widget = MessageWidget(self.mock_message_data, is_sender=True)
        
        # Check sender-specific styling
        assert "sender" in widget.styleSheet().lower()
        assert self.mock_message_data["content"] in widget.message_label.text()
        assert widget.status_label.text() == self.mock_message_data["status"]

    def test_message_widget_receiver_view(self):
        """Test message widget display for receiver."""
        widget = MessageWidget(self.mock_message_data, is_sender=False)
        
        # Check receiver-specific styling
        assert "receiver" in widget.styleSheet().lower()
        assert self.mock_message_data["content"] in widget.message_label.text()
        assert not hasattr(widget, 'status_label')  # Receivers don't see status

    def test_message_widget_selection(self):
        """Test message selection functionality."""
        widget = MessageWidget(self.mock_message_data, is_sender=True)
        
        # Test selection
        widget.set_selected(True)
        assert widget.is_selected
        assert "selected" in widget.styleSheet().lower()
        
        # Test deselection
        widget.set_selected(False)
        assert not widget.is_selected
        assert "selected" not in widget.styleSheet().lower()

    def test_user_list_widget(self):
        """Test user list widget functionality."""
        mock_users = [
            {"username": "user1", "nickname": "User One", "status": "online"},
            {"username": "user2", "nickname": "User Two", "status": "offline"}
        ]
        
        widget = UserListWidget()
        widget.update_users(mock_users)
        
        # Check if all users are displayed
        assert widget.count() == len(mock_users)
        
        # Check if online status is correctly displayed
        first_item = widget.item(0)
        assert "online" in first_item.text().lower()
        
        second_item = widget.item(1)
        assert "offline" in second_item.text().lower()

    def test_message_status_update(self):
        """Test message status updates in message widget."""
        widget = MessageWidget(self.mock_message_data, is_sender=True)
        
        # Test status update
        new_status = "read"
        widget.update_status(new_status)
        assert widget.status_label.text() == new_status
        
        # Test invalid status
        with self.assertRaises(ValueError):
            widget.update_status("invalid_status")

    def test_chat_widget_unread_update(self):
        """Test updating unread count in chat widget."""
        widget = ChatWidget(self.mock_chat_data)
        
        # Update unread count
        new_count = 5
        widget.update_unread_count(new_count)
        assert str(new_count) in widget.unread_label.text()
        
        # Test zero unread messages
        widget.update_unread_count(0)
        assert widget.unread_label.isHidden()

if __name__ == "__main__":
    unittest.main()
