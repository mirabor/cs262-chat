import sqlite3
import bcrypt
from datetime import datetime

DATABASE_FILE = "chat_app.db"

def initialize_database(conn=None):
    """Initialize the database and create necessary tables."""
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DATABASE_FILE)
        close_conn = True

    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nickname TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    # UserConfig table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS userconfig (
            username TEXT UNIQUE NOT NULL,
            msg_view_limit INTEGER DEFAULT 6,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        )
        """
    )

    # Messages table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            read INTEGER DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
        """
    )

    conn.commit()
    if close_conn:
        conn.close()

def hash_password(password):
    """Hash a password for secure storage."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed

def verify_password(plain_password, hashed_password):
    """Verify a plain password against the hashed one."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)

def signup(input_data, conn=None):
    """Sign up a new user."""
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DATABASE_FILE)
        close_conn = True

    try:
        username = input_data.get("username")
        nickname = input_data.get("nickname")
        password = input_data.get("password")

        if not username or not nickname or not password:
            return {"success": False, "error_message": "All fields are required."}

        cursor = conn.cursor()

        # Check if the username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return {"success": False, "error_message": "Username already taken."}

        # Hash the password
        hashed_password = hash_password(password)

        # Insert the new user into the users table
        cursor.execute(
            """
            INSERT INTO users (username, nickname, password)
            VALUES (?, ?, ?)
            """,
            (username, nickname, hashed_password),
        )

        # Set a default message view limit (e.g., 6)
        cursor.execute(
            """
            INSERT INTO userconfig (username, msg_view_limit)
            VALUES (?, ?)
            """,
            (username, 6)
        )

        conn.commit()
        return {"success": True, "error_message": ""}

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

    finally:
        if close_conn:
            conn.close()

def login(login_data):
    """Log in a user and retrieve additional info (nickname and view limit)."""
    try:
        username = login_data.get("username")
        password = login_data.get("password")

        if not username or not password:
            return {"success": False, "error_message": "Username and password are required."}

        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Fetch the user's hashed password and nickname
        cursor.execute(
            "SELECT id, username, nickname, password FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()

        if not user:
            return {"success": False, "error_message": "Invalid username or password."}

        user_id, db_username, db_nickname, hashed_password = user

        # Verify the password
        if not verify_password(password, hashed_password):
            return {"success": False, "error_message": "Invalid username or password."}

        # Fetch the message view limit
        cursor.execute(
            "SELECT msg_view_limit FROM userconfig WHERE username = ?",
            (username,)
        )
        view_limit_row = cursor.fetchone()
        view_limit = view_limit_row[0] if view_limit_row else 6  # Default to 6 if not set

        conn.close()

        return {
            "success": True,
            "error_message": "",
            "user_id": user_id,
            "nickname": db_nickname,
            "view_limit": view_limit
        }

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

def delete_user(user_id):
    """Delete a user and all associated data."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Delete the user from the users table (cascading deletes will handle userconfig and messages)
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )

        conn.commit()
        conn.close()

        return {"success": True, "error_message": ""}

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

# ==================== Chat Management Functions ====================

def get_chats(user_id):
    """Get all chats involving a user, sorted by most recent."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Fetch all messages involving the user
        cursor.execute(
            """
            SELECT * FROM messages
            WHERE sender_id = ? OR receiver_id = ?
            ORDER BY timestamp DESC
            """,
            (user_id, user_id)
        )

        messages = cursor.fetchall()

        # Organize messages into chats
        chats = {}
        for message in messages:
            sender_id = message[1]
            receiver_id = message[2]
            chat_key = f"{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}"

            if chat_key not in chats:
                chats[chat_key] = {
                    "participants": [sender_id, receiver_id],
                    "messages": []
                }

            chats[chat_key]["messages"].append({
                "sender": sender_id,
                "content": message[3],
                "timestamp": message[4],
                "read": message[5]
            })

        conn.close()
        return {"success": True, "chats": chats, "error_message": ""}

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

def get_all_users(exclude_username=None):
    """Get all users except the excluded one."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        if exclude_username:
            cursor.execute("SELECT username FROM users WHERE username != ?", (exclude_username,))
        else:
            cursor.execute("SELECT username FROM users")

        users = [row[0] for row in cursor.fetchall()]

        conn.close()
        return {"success": True, "users": users, "error_message": ""}

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

def update_view_limit(username, new_limit, conn = None):
    """Update the message view limit for a user."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE userconfig
            SET msg_view_limit = ?
            WHERE username = ?
            """,
            (new_limit, username)
        )

        conn.commit()
        conn.close()

        return {"success": True, "error_message": ""}

    except Exception as e:
        return {"success": False, "error_message": f"An error occurred: {str(e)}"}

if __name__ == "__main__":
    initialize_database()

    # Sign up a new user
    signup_response = signup({
        "username": "test_user",
        "nickname": "Test User",
        "password": "password123"
    })
    print("Signup Response:", signup_response)

    # Log in the user
    login_response = login({
        "username": "test_user",
        "password": "password123"
    })
    print("Login Response:", login_response)

    # Update the message view limit
    update_response = update_view_limit("test_user", 10)
    print("Update View Limit Response:", update_response)

    # Get all users
    users_response = get_all_users()
    print("All Users:", users_response)

    # Get chats for a user
    chats_response = get_chats(1)
    print("Chats for User 1:", chats_response)

    # Delete a user
    delete_response = delete_user(1)
    print("Delete User Response:", delete_response)