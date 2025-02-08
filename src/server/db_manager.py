import sqlite3
from datetime import datetime

DATABASE_FILE = "chat_app.db"

class DBManager:
    def __init__(self, db_file=DATABASE_FILE):
        self.db_file = db_file

    def _get_connection(self):
        
        return sqlite3.connect(self.db_file)

    def initialize_database(self, conn = None):
        """Initialize the database and create necessary tables."""
        with self._get_connection() as conn:
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

    def add_user(self, username, nickname, password):
        """
        Add a new user to the database.
        
        Args:
            username (str): The username of the user.
            nickname (str): The nickname of the user.
            password (str): The hashed password of the user.
        
        Returns:
            dict: A dictionary containing success status and error message.
        """
        if not username or not nickname or not password:
            return {"success": False, "error_message": "All fields are required."}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            try:
                # Check if the username already exists
                cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return {"success": False, "error_message": "Username already taken."}

                # Insert the new user into the users table
                cursor.execute(
                    """
                    INSERT INTO users (username, nickname, password)
                    VALUES (?, ?, ?)
                    """,
                    (username, nickname, password),
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

            except sqlite3.Error as e:
                return {"success": False, "error_message": f"Database error: {str(e)}"}

    def login(self, login_data):
        """Log in a user and retrieve additional info (nickname and view limit)."""
        username = login_data.get("username")
        password = login_data.get("password")

        if not username or not password:
            return {"success": False, "error_message": "Username and password are required."}

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Fetch the user's password and nickname
            cursor.execute(
                "SELECT id, username, nickname, password FROM users WHERE username = ?",
                (username,)
            )
            user = cursor.fetchone()

            if not user:
                return {"success": False, "error_message": "Invalid username or password."}

            user_id, db_username, db_nickname, password = user

            # Fetch the message view limit
            cursor.execute(
                "SELECT msg_view_limit FROM userconfig WHERE username = ?",
                (username,)
            )
            view_limit_row = cursor.fetchone()
            view_limit = view_limit_row[0] if view_limit_row else 6  # Default to 6 if not set

            return {
                "success": True,
                "error_message": "",
                "user_id": user_id,
                "nickname": db_nickname,
                "view_limit": view_limit
            }

    def delete_user(self, user_id):
        """Delete a user and all associated data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Delete the user from the users table (cascading deletes will handle userconfig and messages)
            cursor.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )

            conn.commit()
            return {"success": True, "error_message": ""}

    def get_chats(self, user_id):
        """Get all chats involving a user, sorted by most recent."""
        with self._get_connection() as conn:
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

            return {"success": True, "chats": chats, "error_message": ""}

    def get_all_users(self, exclude_username=None):
        """Get all users except the excluded one."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if exclude_username:
                cursor.execute("SELECT username FROM users WHERE username != ?", (exclude_username,))
            else:
                cursor.execute("SELECT username FROM users")

            users = [row[0] for row in cursor.fetchall()]
            return {"success": True, "users": users, "error_message": ""}

    def update_view_limit(self, username, new_limit):
        """Update the message view limit for a user."""
        with self._get_connection() as conn:
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
            return {"success": True, "error_message": ""}