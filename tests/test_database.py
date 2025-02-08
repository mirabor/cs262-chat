import sqlite3
import pytest
from datetime import datetime
from src.server.db_manager import DBManager
from src.server.api import signup, login, delete_user, get_chats, update_view_limit, get_all_users

@pytest.fixture
def db_manager():
    """Fixture to initialize and clean up the database."""
    db_manager = DBManager()
    db_manager.initialize_database()
    yield db_manager
    # Clean up the database after each test
    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM userconfig")
        cursor.execute("DELETE FROM messages")
        conn.commit()
        
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

def test_signup(db_manager):
    """Test the signup function."""
    input_data = {
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    }
    response = db_manager.add_user(**input_data)
    assert response["success"] is True

def test_login(db_manager):
    """Test the login function."""
    signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    })

    login_data = {
        "username": "test_user",
        "password": "password123"
    }
    response = login(login_data)
    assert response["success"] is True
    assert response["error_message"] == ""

def test_delete_user(db_manager):
    """Test the delete_user function."""
    signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    })

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("test_user",))
        user_id = cursor.fetchone()[0]

    response = delete_user(user_id)
    assert response["success"] is True

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        assert cursor.fetchone() is None

def test_get_chats(db_manager):
    """Test the get_chats function."""
    signup({
        "username": "user1",
        "nickname": "User One",
        "password": "password123"
    })

    signup({
        "username": "user2",
        "nickname": "User Two",
        "password": "password123"
    })

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
        user1_id = cursor.fetchone()[0]

        cursor.execute("SELECT id FROM users WHERE username = ?", ("user2",))
        user2_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO messages (sender_id, receiver_id, content, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (user1_id, user2_id, "Hello, User Two!", datetime.now().isoformat())
        )
        conn.commit()

    response = get_chats(user1_id)
    assert response["success"] is True
    assert len(response["chats"]) == 1

def test_update_view_limit(db_manager):
    """Test the update_view_limit function."""
    signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    })

    response = update_view_limit("test_user", 10)
    assert response["success"] is True

    with db_manager._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT msg_view_limit FROM userconfig WHERE username = ?", ("test_user",))
        limit = cursor.fetchone()[0]
        assert limit == 10

def test_get_all_users(db_manager):
    """Test the get_all_users function."""
    db_manager.add_user(
        username="user1",
        nickname="User One",
        password="password123"
    )
    
    db_manager.add_user(
        username="user2",
        nickname="User Two",
        password="password123"
    )
    
    response = db_manager.get_all_users()
    assert response["success"] is True
    assert len(response["users"]) == 2