"""Test cases for the message delivery system."""

import pytest
from datetime import datetime
from src.server.db_manager import DBManager
import os

@pytest.fixture
def db_manager():
    """Create a test database manager with a temporary database file."""
    test_db = "test_message_system.db"
    if os.path.exists(test_db):
        os.remove(test_db)
    
    manager = DBManager(test_db)
    manager.initialize_database()
    yield manager
    
    # Clean up
    if os.path.exists(test_db):
        os.remove(test_db)

@pytest.fixture
def sample_users(db_manager):
    """Create sample users for testing."""
    users = [
        ("user1", "User One", "password1"),
        ("user2", "User Two", "password2"),
        ("user3", "User Three", "password3")
    ]
    for username, nickname, password in users:
        db_manager.add_user(username, nickname, password)
        db_manager.update_view_limit(username, 10)  # Default limit
    yield users
    
    # Clean up users
    for username, _, _ in users:
        try:
            db_manager.delete_user(username)
        except:
            pass

def test_message_delivery_system(db_manager, sample_users):
    """Test the message delivery system with user message limits."""
    # Set different message limits for users
    db_manager.update_view_limit("user1", 2)
    db_manager.update_view_limit("user2", 5)
    
    # Send multiple messages
    messages = [
        ("user1", "user2", "Message 1"),
        ("user1", "user2", "Message 2"),
        ("user1", "user2", "Message 3"),
        ("user2", "user1", "Reply 1"),
        ("user2", "user1", "Reply 2"),
        ("user2", "user1", "Reply 3"),
    ]
    
    for sender, receiver, content in messages:
        db_manager.add_message(sender, receiver, content)
    
    # Check message delivery respects limits
    user1_messages = db_manager.get_messages("user1")
    assert len(user1_messages) <= 2  # user1's limit
    
    user2_messages = db_manager.get_messages("user2")
    assert len(user2_messages) <= 5  # user2's limit

def test_message_status_updates(db_manager, sample_users):
    """Test message status transitions (sent -> delivered -> read)."""
    # Send a message
    db_manager.add_message("user1", "user2", "Test message")
    
    # Get the message ID
    messages = db_manager.get_messages("user2")
    msg_id = messages[0]["msg_id"]
    
    # Check initial status
    assert messages[0]["status"] == "sent"
    
    # Mark as delivered
    db_manager.update_message_status(msg_id, "delivered")
    messages = db_manager.get_messages("user2")
    assert messages[0]["status"] == "delivered"
    
    # Mark as read
    db_manager.update_message_status(msg_id, "read")
    messages = db_manager.get_messages("user2")
    assert messages[0]["status"] == "read"

def test_message_ordering(db_manager, sample_users):
    """Test that messages are retrieved in correct chronological order."""
    # Send messages with delays
    messages = [
        ("user1", "user2", "First message"),
        ("user2", "user1", "Second message"),
        ("user1", "user2", "Third message")
    ]
    
    for sender, receiver, content in messages:
        db_manager.add_message(sender, receiver, content)
    
    # Get messages for user2
    user2_messages = db_manager.get_messages("user2")
    
    # Verify order
    assert len(user2_messages) == 2  # Should only see messages sent to user2
    assert user2_messages[0]["content"] == "First message"
    assert user2_messages[1]["content"] == "Third message"

def test_message_deletion(db_manager, sample_users):
    """Test message deletion functionality."""
    # Send messages
    db_manager.add_message("user1", "user2", "Message 1")
    db_manager.add_message("user1", "user2", "Message 2")
    
    # Get message IDs
    messages = db_manager.get_messages("user2")
    msg_ids = [msg["msg_id"] for msg in messages]
    
    # Delete one message
    db_manager.delete_message(msg_ids[0])
    
    # Verify message was deleted
    updated_messages = db_manager.get_messages("user2")
    assert len(updated_messages) == 1
    assert updated_messages[0]["msg_id"] == msg_ids[1]

def test_message_limit_updates(db_manager, sample_users):
    """Test behavior when user's message limit is changed."""
    # Set initial limit and send messages
    db_manager.update_view_limit("user1", 5)
    
    for i in range(6):
        db_manager.add_message("user2", "user1", f"Message {i}")
    
    # Check initial message count
    messages = db_manager.get_messages("user1")
    assert len(messages) == 5
    
    # Reduce limit
    db_manager.update_view_limit("user1", 3)
    
    # Check message count after limit reduction
    messages = db_manager.get_messages("user1")
    assert len(messages) == 3
    
    # Increase limit
    db_manager.update_view_limit("user1", 6)
    
    # Check message count after limit increase
    messages = db_manager.get_messages("user1")
    assert len(messages) == 6  # Should now see all messages

def test_message_delivery_to_offline_user(db_manager, sample_users):
    """Test message delivery when recipient is offline."""
    # Set user2 as offline
    db_manager.set_user_status("user2", False)
    
    # Send message to offline user
    db_manager.add_message("user1", "user2", "Message to offline user")
    
    # Check message status
    messages = db_manager.get_messages("user2")
    assert messages[0]["status"] == "sent"  # Should be marked as sent, not delivered
    
    # Set user2 as online
    db_manager.set_user_status("user2", True)
    
    # Message should now be marked as delivered
    messages = db_manager.get_messages("user2")
    assert messages[0]["status"] == "delivered"
