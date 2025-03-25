import pytest
import sqlite3
import os
from datetime import datetime, timedelta

from src.services.db_manager import DBManager


@pytest.fixture
def db_manager():
    """Create a test database manager with a temporary database file."""
    test_db = "test_chat_app_extended.db"
    # Ensure the test database doesn't exist
    if os.path.exists(test_db):
        os.remove(test_db)
    
    manager = DBManager(test_db)
    manager.initialize_database()
    yield manager
    
    # Clean up the database after each test
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
    return users


@pytest.fixture
def sample_messages(db_manager, sample_users):
    """Create sample messages between users."""
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        # Get user IDs
        cursor.execute("SELECT username FROM users")
        usernames = [row[0] for row in cursor.fetchall()]
        
        # Create messages
        now = datetime.now()
        messages = [
            (usernames[0], usernames[1], "Hello from user1", now.isoformat()),
            (usernames[1], usernames[0], "Hello from user2", now.isoformat()),
            (usernames[0], usernames[2], "Hello to user3", now.isoformat()),
            (usernames[2], usernames[0], "Hello back from user3", now.isoformat())
        ]
        
        for sender, receiver, content, timestamp in messages:
            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (sender, receiver, content, timestamp)
            )
        
        conn.commit()
    return messages


def test_start_chat(db_manager, sample_users):
    """Test starting a new chat between users."""
    result = db_manager.start_chat("user1", "user2")
    
    assert result["success"] is True
    assert result["chat_id"] == "user1_user2"
    assert result["error_message"] == ""


def test_start_chat_existing(db_manager, sample_users, sample_messages):
    """Test starting a chat that already exists."""
    result = db_manager.start_chat("user1", "user2")
    
    assert result["success"] is True
    assert result["chat_id"] == "user1_user2"
    assert result["error_message"] == ""


def test_get_user_message_limit(db_manager, sample_users):
    """Test retrieving a user's message view limit."""
    result = db_manager.get_user_message_limit("user1")
    
    assert result["message_limit"] == "6"  # Default value
    assert result["error_message"] == ""


def test_get_user_message_limit_nonexistent(db_manager):
    """Test retrieving message limit for a non-existent user."""
    result = db_manager.get_user_message_limit("nonexistent")
    
    assert result["message_limit"] == "6"  # Default value
    assert result["error_message"] == ""


def test_delete_messages(db_manager, sample_users, sample_messages):
    """Test deleting specific messages from a chat."""
    # First get messages to find indices
    chat_id = "user1_user2"
    messages_result = db_manager.get_messages(chat_id, "user1")
    assert messages_result["success"] is True
    assert len(messages_result["messages"]) > 0
    
    # Delete the first message
    result = db_manager.delete_messages(chat_id, [0], "user1")
    
    assert result["success"] is True
    assert result["error_message"] == ""
    
    # Verify message was deleted
    updated_messages = db_manager.get_messages(chat_id, "user1")
    assert len(updated_messages["messages"]) == len(messages_result["messages"]) - 1


def test_delete_messages_with_list_chat_id(db_manager, sample_users, sample_messages):
    """Test deleting messages with a list-type chat_id."""
    chat_id = ["user1_user2"]
    result = db_manager.delete_messages(chat_id, [0], "user1")
    
    assert result["success"] is True
    assert result["error_message"] == ""


def test_delete_messages_invalid_index(db_manager, sample_users, sample_messages):
    """Test deleting a message with an invalid index."""
    chat_id = "user1_user2"
    # Try to delete a message with an index that's out of range
    result = db_manager.delete_messages(chat_id, [100], "user1")
    
    assert result["success"] is True
    assert result["error_message"] == ""


def test_get_messages(db_manager, sample_users, sample_messages):
    """Test retrieving messages for a specific chat."""
    chat_id = "user1_user2"
    result = db_manager.get_messages(chat_id, "user1")
    
    assert result["success"] is True
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0
    assert result["error_message"] == ""
    
    # Check message structure
    message = result["messages"][0]
    assert "id" in message
    assert "sender" in message
    assert "receiver" in message
    assert "content" in message
    assert "timestamp" in message
    assert "read" in message


def test_get_messages_with_list_chat_id(db_manager, sample_users, sample_messages):
    """Test retrieving messages with a list-type chat_id."""
    chat_id = ["user1_user2"]
    result = db_manager.get_messages(chat_id, "user1")
    
    assert result["success"] is True
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) > 0


def test_get_messages_empty_chat(db_manager, sample_users):
    """Test retrieving messages for an empty chat."""
    chat_id = "user1_user3"  # Assuming no messages between these users
    result = db_manager.get_messages(chat_id, "user1")
    
    assert result["success"] is True
    assert isinstance(result["messages"], list)
    assert len(result["messages"]) == 0
    assert result["error_message"] == ""


def test_send_chat_message(db_manager, sample_users):
    """Test sending a chat message."""
    chat_id = "user1_user2"
    result = db_manager.send_chat_message(chat_id, "user1", "Hello, this is a test message")
    
    assert result["success"] is True
    assert result["error_message"] == ""
    
    # Verify message was sent
    messages = db_manager.get_messages(chat_id, "user1")
    assert len(messages["messages"]) > 0
    assert messages["messages"][-1]["content"] == "Hello, this is a test message"
    assert messages["messages"][-1]["sender"] == "user1"
    assert messages["messages"][-1]["receiver"] == "user2"


def test_send_chat_message_with_list_chat_id(db_manager, sample_users):
    """Test sending a message with a list-type chat_id."""
    chat_id = ["user1_user2"]
    result = db_manager.send_chat_message(chat_id, "user1", "Hello with list chat_id")
    
    assert result["success"] is True
    assert result["error_message"] == ""


def test_send_chat_message_missing_fields(db_manager):
    """Test sending a message with missing fields."""
    # Missing content
    result1 = db_manager.send_chat_message("user1_user2", "user1", "")
    assert result1["success"] is False
    
    # Missing sender
    result2 = db_manager.send_chat_message("user1_user2", "", "content")
    assert result2["success"] is False
    
    # Missing chat_id
    result3 = db_manager.send_chat_message("", "user1", "content")
    assert result3["success"] is False


def test_send_chat_message_nonexistent_recipient(db_manager, sample_users):
    """Test sending a message to a non-existent recipient."""
    # Delete user2
    db_manager.delete_user("user2")
    
    # Try to send a message to the deleted user
    result = db_manager.send_chat_message("user1_user2", "user1", "Hello, are you there?")
    
    assert result["success"] is False
    assert "deleted their account" in result["error_message"]


def test_get_users_to_display(db_manager, sample_users):
    """Test retrieving users to display."""
    result = db_manager.get_users_to_display("user1")
    
    assert result["success"] is True
    assert isinstance(result["users"], list)
    assert len(result["users"]) == 2  # user2 and user3, excluding user1
    assert "user1" not in result["users"]
    assert "user2" in result["users"]
    assert "user3" in result["users"]
    assert result["error_message"] == ""


def test_get_users_to_display_with_search(db_manager, sample_users):
    """Test retrieving users with a search pattern."""
    result = db_manager.get_users_to_display("user1", search_pattern="2")
    
    assert result["success"] is True
    assert len(result["users"]) == 1
    assert "user2" in result["users"]
    assert "user3" not in result["users"]


def test_get_users_to_display_with_pagination(db_manager, sample_users):
    """Test retrieving users with pagination."""
    # Add more users to test pagination
    for i in range(4, 15):
        db_manager.add_user(f"user{i}", f"User {i}", f"password{i}")
    
    # Get first page (users_per_page=5)
    result1 = db_manager.get_users_to_display("user1", page=1, users_per_page=5)
    assert result1["success"] is True
    assert len(result1["users"]) == 5
    
    # Get second page
    result2 = db_manager.get_users_to_display("user1", page=2, users_per_page=5)
    assert result2["success"] is True
    assert len(result2["users"]) == 5
    
    # Ensure pages don't overlap
    assert set(result1["users"]).isdisjoint(set(result2["users"]))


def test_save_settings(db_manager, sample_users):
    """Test saving user settings."""
    result = db_manager.save_settings("user1", 10)
    
    assert result["success"] is True
    assert result["error_message"] == ""
    
    # Verify settings were saved
    limit_result = db_manager.get_user_message_limit("user1")
    assert limit_result["message_limit"] == "10"
