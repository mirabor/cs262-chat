import sqlite3
import pytest
from datetime import datetime
from src.server.database import initialize_database, signup, login, delete_user, get_chats, update_view_limit, get_all_users

@pytest.fixture(scope="function", autouse=True)
def db():
    """Fixture to create a new in-memory database for each test."""
    conn = sqlite3.connect(":memory:")
    initialize_database(conn)
    yield conn
    conn.rollback()  # Roll back any remaining transactions
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("DROP TABLE IF EXISTS userconfig")
    conn.execute("DROP TABLE IF EXISTS messages")
    conn.close()

def test_initialize_database(db):
    """Test that the database is initialized correctly."""
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='userconfig'")
    assert cursor.fetchone() is not None

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
    assert cursor.fetchone() is not None

def test_signup(db):
    """Test the signup function."""
    input_data = {
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    }
    response = signup(input_data, db)
    assert response["success"] is True

def test_login(db):
    """Test the login function."""
    signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    }, db)

    login_data = {
        "username": "test_user",
        "password": "password123"
    }
    response = login(login_data, db)
    assert response["success"] is True
    assert response["error_message"] == ""

# def test_delete_user(db, conn = None):
#     """Test the delete_user function."""
#     signup({
#         "username": "test_user",
#         "nickname": "Test User",
#         "password": "password123"
#     }, db)

#     cursor = db.cursor()
#     cursor.execute("SELECT id FROM users WHERE username = ?", ("test_user",))
#     user_id = cursor.fetchone()[0]

#     response = delete_user(user_id, db)
#     assert response["success"] is True

#     cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
#     assert cursor.fetchone() is None

# def test_get_chats(db, conn = None):
#     """Test the get_chats function."""
#     signup({
#         "username": "user1",
#         "nickname": "User One",
#         "password": "password123"
#     }, db)

#     signup({
#         "username": "user2",
#         "nickname": "User Two",
#         "password": "password123"
#     }, db)

    # cursor = db.cursor()
    # cursor.execute("SELECT id FROM users WHERE username = ?", ("user1",))
    # user1_id = cursor.fetchone()[0]

    # cursor.execute("SELECT id FROM users WHERE username = ?", ("user2",))
    # user2_id = cursor.fetchone()[0]

    # cursor.execute(
    #     """
    #     INSERT INTO messages (sender_id, receiver_id, content, timestamp)
    #     VALUES (?, ?, ?, ?)
    #     """,
    #     (user1_id, user2_id, "Hello, User Two!", datetime.now().isoformat())
    # )
    # db.commit()

    # response = get_chats(user1_id, db)
    # assert response["success"] is True
    # assert len(response["chats"]) == 1

# def test_update_view_limit(db):
#     """Test the update_view_limit function."""
#     signup({
#         "username": "test_user",
#         "nickname": "Test User",
#         "password": "password123"
#     }, db)

#     response = update_view_limit("test_user", 10, db)
#     assert response["success"] is True

#     cursor = db.cursor()
#     cursor.execute("SELECT msg_view_limit FROM userconfig WHERE username = ?", ("test_user",))
#     limit = cursor.fetchone()[0]
#     assert limit == 10

def test_get_all_users(db):
    """Test the get_all_users function."""
    signup({
        "username": "user1",
        "nickname": "User One",
        "password": "password123"
    }, db)

    signup({
        "username": "user2",
        "nickname": "User Two",
        "password": "password123"
    }, db)

    response = get_all_users(db)
    assert response["success"] is True
    assert len(response["users"]) == 2