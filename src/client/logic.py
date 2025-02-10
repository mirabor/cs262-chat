import json
import os
from datetime import datetime
from src.client.utils import hash_password, verify_password
from fnmatch import fnmatch


class ChatAppLogic:
    def __init__(self):
        self.current_user = None
        self.load_data()

    def delete_chats(self, chat_ids):
        for chat_id in chat_ids:
            del self.chats[chat_id]
        self.save_data()

    def delete_messages(self, chat_id, message_indices, current_user):
        unauthorized_attempt = False

        for i in sorted(message_indices, reverse=True):
            if self.chats[chat_id]["messages"][i]["sender"] == current_user:
                del self.chats[chat_id]["messages"][i]
            else:
                # Mark if unauthorized deletion was attempted
                unauthorized_attempt = True

        self.save_data()

        if unauthorized_attempt:
            return False, "You can only delete messages that you sent."
        return True, "Messages deleted successfully."

    def send_message(self, chat_id, sender, content):
        self.chats[chat_id]["messages"].append(
            {
                "sender": sender,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "read": False,
            }
        )
        self.save_data()

    def login(self, username, password):
        if username in self.users:
            stored_password = self.users[username]["password"]
            if verify_password(password, stored_password):
                self.current_user = username
                return True
        return False

    def signup(self, username, nickname, password):
        if not username or not nickname or not password:
            return False
        if username in self.users:
            return False
        hashed_password = hash_password(password)
        self.users[username] = {
            "nickname": nickname,
            "password": hashed_password,
            "message_limit": 6,
        }
        self.save_data()
        return True

    def save_settings(self, username, message_limit):
        if username in self.users:
            self.users[username]["message_limit"] = message_limit
            self.save_data()

    def start_chat(self, current_user, other_user):
        chat_id = f"{min(current_user, other_user)}_{max(current_user, other_user)}"
        if chat_id not in self.chats:
            self.chats[chat_id] = {
                "participants": [current_user, other_user],
                "messages": [],
            }
            self.save_data()
        return chat_id

    def get_users_to_display(
        self, current_user, search_pattern, current_page, users_per_page
    ):
        # If search pattern is empty, return all users except the current user
        if not search_pattern:
            self.filtered_users = [
                username for username in self.users if username != current_user
            ]
        else:
            # Filter users based on the search pattern
            self.filtered_users = [
                username
                for username in self.users
                if username != current_user and fnmatch(username, f"*{search_pattern}*")
            ]

        # Calculate the subset of users to display
        start_index = current_page * users_per_page
        end_index = start_index + users_per_page
        return self.filtered_users[start_index:end_index]

    def load_data(self):
        if not os.path.exists("users.json"):
            with open("users.json", "w") as f:
                json.dump({}, f)
        if not os.path.exists("chats.json"):
            with open("chats.json", "w") as f:
                json.dump({}, f)

        with open("users.json", "r") as f:
            self.users = json.load(f)
        with open("chats.json", "r") as f:
            self.chats = json.load(f)

    def save_data(self):
        with open("users.json", "w") as f:
            json.dump(self.users, f)
        with open("chats.json", "w") as f:
            json.dump(self.chats, f)

    def delete_account(self, current_user):
        del self.users[current_user]

        # Remove user from all chats

        # NOTE: (DOCS) This means, users who interacted with with curr user
        # will lose all chats/messages
        for chat_id in list(self.chats.keys()):
            if current_user in self.chats[chat_id]["participants"]:
                del self.chats[chat_id]
        self.save_data()

    def get_user_message_limit(self, current_user):
        return str(self.users[current_user].get("message_limit", ""))
