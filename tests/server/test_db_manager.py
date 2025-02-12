"""Test cases for the database manager."""

import pytest
import sqlite3
import os
from datetime import datetime
from src.server.db_manager import DBManager

@pytest.fixture
def db_manager():
    """Create a test database manager with a temporary database file."""
    test_db = "test_chat_app.db"
    # Ensure the test database doesn't exist
    if os.path.exists(test_db):
        os.remove(test_db)
    
    manager = DBManager(test_db)
    manager.initialize_database()
    yield manager
    
    # Clean up the database after each test
    with manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM userconfig")
        cursor.execute("DELETE FROM messages")
        conn.commit()
    
    # Remove test database
    if os.path.exists(test_db):
        os.remove(test_db)

def test_initialize_database(db_manager):
    """Test that the database is initialized correctly."""
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        assert cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='userconfig'")
        assert cursor.fetchone() is not None

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        assert cursor.fetchone() is not None

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

# Happy Path Tests

def test_add_user_success(db_manager):
    """Test successful user addition."""
    result = db_manager.add_user("testuser", "Test User", "password123")
    assert result["success"] is True
    assert result["error_message"] == ""

    # Verify user was added
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, nickname FROM users WHERE username = ?", ("testuser",))
        user = cursor.fetchone()
        assert user == ("testuser", "Test User")

def test_login_success(db_manager, sample_users):
    """Test successful login."""
    login_data = {"username": "user1", "password": "password1"}
    result = db_manager.login(login_data)
    
    assert result["success"] is True
    assert result["error_message"] == ""
    assert result["nickname"] == "User One"
    assert result["view_limit"] == 6  # Default view limit

def test_get_chats_empty(db_manager, sample_users):
    """Test getting chats when no messages exist."""
    result = db_manager.get_chats(1)  # user1's ID should be 1
    assert result["success"] is True
    assert result["chats"] == {}

def test_get_chats(db_manager):
    """Test the get_chats function with messages."""
    # Create two users
    db_manager.add_user("user1", "User One", "password123")
    db_manager.add_user("user2", "User Two", "password123")

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
        user1_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM users WHERE username = ?", ("user2",))
        user2_id = cursor.fetchone()[0]

        # Add a test message
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user1_id, user2_id, "Hello, User Two!", datetime.now().isoformat())
        )
        conn.commit()

    response = db_manager.get_chats(user1_id)
    assert response["success"] is True
    assert len(response["chats"]) == 1
    
    # Verify message content
    chat_key = f"{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
    chat = response["chats"][chat_key]
    assert len(chat["messages"]) == 1
    assert chat["messages"][0]["content"] == "Hello, User Two!"
    assert chat["messages"][0]["sender"] == user1_id

def test_get_all_users(db_manager, sample_users):
    """Test getting all users except excluded one."""
    result = db_manager.get_all_users(exclude_username="user1")
    assert result["success"] is True
    assert set(result["users"]) == {"user2", "user3"}

def test_update_view_limit(db_manager, sample_users):
    """Test updating message view limit."""
    result = db_manager.save_settings("user1", 10)
    assert result["success"] is True
    
    # Verify the update
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT msg_view_limit FROM userconfig WHERE username = ?", ("user1",))
        limit = cursor.fetchone()[0]
        assert limit == 10

def test_delete_user(db_manager, sample_users):
    """Test deleting a user."""
    # First get the user's ID
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
        user_id = cursor.fetchone()[0]
    
    result = db_manager.delete_user(user_id)
    assert result["success"] is True
    
    # Verify user was deleted
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        assert cursor.fetchone() is None

def test_mark_message_as_read(db_manager):
    """Test marking a message as read."""
    # Create two users
    db_manager.add_user("user1", "User One", "password123")
    db_manager.add_user("user2", "User Two", "password123")

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
        user1_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM users WHERE username = ?", ("user2",))
        user2_id = cursor.fetchone()[0]

        # Add a test message
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user1_id, user2_id, "Hello, User Two!", datetime.now().isoformat())
        )
        conn.commit()

    # Mark the message as read
    result = db_manager.mark_message_as_read(user2_id, user1_id)
    assert result["success"] is True

    # Verify the message status
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM messages WHERE sender_id = ? AND receiver_id = ?", (user1_id, user2_id))
        status = cursor.fetchone()[0]
        assert status == "read"

def test_mark_message_as_unread(db_manager):
    """Test marking a message as unread."""
    # Create two users
    db_manager.add_user("user1", "User One", "password123")
    db_manager.add_user("user2", "User Two", "password123")

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
        user1_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM users WHERE username = ?", ("user2",))
        user2_id = cursor.fetchone()[0]

        # Add a test message
        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user1_id, user2_id, "Hello, User Two!", datetime.now().isoformat())
        )
        conn.commit()

    # Mark the message as read
    result = db_manager.mark_message_as_read(user2_id, user1_id)
    assert result["success"] is True

    # Mark the message as unread
    result = db_manager.mark_message_as_unread(user2_id, user1_id)
    assert result["success"] is True

    # Verify the message status
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM messages WHERE sender_id = ? AND receiver_id = ?", (user1_id, user2_id))
        status = cursor.fetchone()[0]
        assert status == "unread"

# Edge Cases and Error Tests

def test_add_user_duplicate(db_manager, sample_users):
    """Test adding a user with an existing username."""
    result = db_manager.add_user("user1", "Another User", "password456")
    assert result["success"] is False
    assert "Username already taken" in result["error_message"]

def test_add_user_missing_fields(db_manager):
    """Test adding a user with missing fields."""
    result = db_manager.add_user("", "Test User", "password123")
    assert result["success"] is False
    assert "All fields are required" in result["error_message"]
    
    result = db_manager.add_user("testuser", "", "password123")
    assert result["success"] is False
    assert "All fields are required" in result["error_message"]
    
    result = db_manager.add_user("testuser", "Test User", "")
    assert result["success"] is False
    assert "All fields are required" in result["error_message"]

def test_login_invalid_credentials(db_manager, sample_users):
    """Test login with invalid credentials."""
    # Test non-existent user
    result = db_manager.login({"username": "nonexistent", "password": "password123"})
    assert result["success"] is False
    assert "Invalid username or password" in result["error_message"]
    
    # Test wrong password
    result = db_manager.login({"username": "user1", "password": "wrongpassword"})
    assert result["success"] is False
    assert "Invalid username or password" in result["error_message"]

def test_login_missing_fields(db_manager):
    """Test login with missing fields."""
    result = db_manager.login({"username": "", "password": "password123"})
    assert result["success"] is False
    assert "Username and password are required" in result["error_message"]
    
    result = db_manager.login({"username": "user1", "password": ""})
    assert result["success"] is False
    assert "Username and password are required" in result["error_message"]

def test_delete_nonexistent_user(db_manager):
    """Test deleting a non-existent user."""
    result = db_manager.delete_user(999)  # Non-existent ID
    assert result["success"] is True  # SQLite DELETE is idempotent

def test_update_view_limit_invalid_user(db_manager):
    """Test updating view limit for non-existent user."""
    result = db_manager.save_settings("nonexistent", 10)
    assert result["success"] is True  # SQLite UPDATE is idempotent when no rows match

def test_get_all_users_empty_db(db_manager):
    """Test getting all users from empty database."""
    result = db_manager.get_all_users()
    assert result["success"] is True
    assert result["users"] == []

def test_database_connection_error(db_manager):
    """Test handling of database connection errors."""
    # Create an invalid database path
    invalid_db = DBManager("/nonexistent/path/db.sqlite")
    
    # Test various operations
    with pytest.raises(sqlite3.OperationalError):
        invalid_db.add_user("testuser", "Test User", "password123")
    
    with pytest.raises(sqlite3.OperationalError):
        invalid_db.login({"username": "testuser", "password": "password123"})
    
    with pytest.raises(sqlite3.OperationalError):
        invalid_db.get_all_users()

def test_sql_injection_prevention(db_manager):
    """Test prevention of SQL injection attacks."""
    # Try SQL injection in username
    result = db_manager.add_user("user' OR '1'='1", "Hacker", "password123")
    assert result["success"] is True  # Should treat entire string as username
    
    # Verify no data leak
    login_result = db_manager.login({
        "username": "' OR '1'='1",
        "password": "' OR '1'='1"
    })
    assert login_result["success"] is False  # Should not allow login

def test_concurrent_database_access(db_manager):
    """Test concurrent database access."""
    import threading
    
    def add_user(username):
        db_manager.add_user(username, f"User {username}", "password123")
    
    # Create multiple threads to add users concurrently
    threads = []
    for i in range(10):
        thread = threading.Thread(target=add_user, args=(f"concurrent_user_{i}",))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify all users were added correctly
    result = db_manager.get_all_users()
    assert result["success"] is True
    assert len(result["users"]) == 10
    
    # Verify no duplicate users were created
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT username) FROM users")
        distinct_count = cursor.fetchone()[0]
        assert distinct_count == 10
