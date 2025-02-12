import sqlite3
from datetime import datetime
from src.client.utils import hash_password, verify_password

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

        print(f"Login data: {login_data}")
        print(f"Username: {username}")
        print(f"Password: {password}")

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

            user_id, db_username, db_nickname, db_password = user
            print(f"Stored hashed password from login: {db_password}")

            # Verify the password
            if not verify_password(password, db_password):
                return {"success": False, "error_message": "Invalid username or password."}

            print("Password verification succeeded")
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
        
    def start_chat(self, current_user, other_user):
        """Create a new chat between two users."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Generate a unique chat ID
            chat_id = f"{min(current_user, other_user)}_{max(current_user, other_user)}"

            # Check if the chat already exists
            cursor.execute(
                """
                SELECT id FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                OR (sender_id = ? AND receiver_id = ?)
                LIMIT 1
                """,
                (current_user, other_user, other_user, current_user)
            )
            if cursor.fetchone():
                return {"success": True, "chat_id": chat_id, "error_message": ""}

            # Insert a new message to create the chat
            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (current_user, other_user, "Chat started", datetime.now().isoformat())
            )

            conn.commit()
            return {"success": True, "chat_id": chat_id, "error_message": ""}

    def get_user_message_limit(self, username):
        """Retrieve the message view limit for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT msg_view_limit FROM userconfig WHERE username = ?",
                (username,)
            )
            view_limit_row = cursor.fetchone()
            view_limit = view_limit_row[0] if view_limit_row else 6  # Default to 6 if not set

            return str(view_limit)  # Return the message limit as a string
        
    def delete_chats(self, chat_ids):
        """Delete one or more chats."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            for chat_id in chat_ids:
                # Delete all messages in the chat
                cursor.execute(
                    "DELETE FROM messages WHERE id IN (SELECT id FROM messages WHERE sender_id = ? OR receiver_id = ?)",
                    (chat_id.split("_")[0], chat_id.split("_")[1])
                )

            conn.commit()
            return {"success": True, "error_message": ""}

    def delete_messages(self, chat_id, message_indices, current_user):
        """Delete specific messages from a chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Fetch all messages in the chat
            cursor.execute(
                """
                SELECT id FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp
                """,
                (chat_id.split("_")[0], chat_id.split("_")[1], chat_id.split("_")[1], chat_id.split("_")[0])
            )
            messages = cursor.fetchall()

            # Delete the specified messages
            for i in message_indices:
                if i < len(messages):
                    cursor.execute(
                        "DELETE FROM messages WHERE id = ?",
                        (messages[i][0],)
                    )

            conn.commit()
            return {"success": True, "error_message": ""}

    def get_messages(self, chat_id):
        """Retrieve messages for a specific chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                OR (sender_id = ? AND receiver_id = ?)
                ORDER BY timestamp
                """,
                (chat_id.split("_")[0], chat_id.split("_")[1], chat_id.split("_")[1], chat_id.split("_")[0])
            )
            messages = cursor.fetchall()

            return {"success": True, "messages": messages, "error_message": ""}

    def get_other_user_in_chat(self, chat_id, current_user):
        """Get the other participant in a chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT sender_id, receiver_id FROM messages
                WHERE (sender_id = ? AND receiver_id = ?)
                OR (sender_id = ? AND receiver_id = ?)
                LIMIT 1
                """,
                (chat_id.split("_")[0], chat_id.split("_")[1], chat_id.split("_")[1], chat_id.split("_")[0])
            )
            participants = cursor.fetchone()

            if participants:
                return participants[0] if participants[1] == current_user else participants[1]
            else:
                return "Unknown User"

    def send_chat_message(self, chat_id, sender, content):
        """Send a message in a chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, content, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (sender, chat_id.split("_")[1] if sender == chat_id.split("_")[0] else chat_id.split("_")[0], content, datetime.now().isoformat())
            )

            conn.commit()
            return {"success": True, "error_message": ""}

    def get_users_to_display(self, search_pattern="", page=1, users_per_page=10):
        """Retrieve a list of users with optional filtering and pagination."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if search_pattern:
                cursor.execute(
                    "SELECT username FROM users WHERE username LIKE ? LIMIT ? OFFSET ?",
                    (f"%{search_pattern}%", users_per_page, (page - 1) * users_per_page)
                )
            else:
                cursor.execute(
                    "SELECT username FROM users LIMIT ? OFFSET ?",
                    (users_per_page, (page - 1) * users_per_page)
                )

            users = [row[0] for row in cursor.fetchall()]
            return {"success": True, "users": users, "error_message": ""}