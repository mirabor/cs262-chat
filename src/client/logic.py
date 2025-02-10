import json
import os
from datetime import datetime
from .utils import hash_password, verify_password
from fnmatch import fnmatch
from src.client.client import Client

class ChatAppLogic:
    def __init__(self):
        self.current_user = None
        self.client = Client

    def delete_chats(self, chat_ids):
        """Send a request to delete chats."""
        Client.send_message({
            "action": "delete_chats",
            "chat_ids": chat_ids
        })
        response = Client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def delete_messages(self, chat_id, message_indices, current_user):
        # TODO: error handling for messages trying to be deleted if not from that user
        unauthorized_attempt = False
        Client.send_message({
            "action": "delete_messages",
            "chat_id": chat_id,
            "message_indices": message_indices,
            "current_user": current_user
        })
        response = Client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def login(self, username, password):
        if not username or not password:
            return False
        hashed_password = hash_password(password)
        Client.send_message({
        "action": "login",
        "username": username,
        "password": hashed_password
        })
        response = Client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def signup(self, username, nickname, password):
        if not username or not nickname or not password:
            return False
        if username in self.users:
            return False
        hashed_password = hash_password(password)
        self.send_message({
            "action": "signup",
            "username": username,
            "nickname": nickname,
            "password": hashed_password
        })
        response = self.receive_message()
        return response.get("success"), response.get("error_message", "")

    def save_settings(self, username, message_limit):
        Client.send_message({
            "action": "save_settings",
            "username": username,
            "message_limit": message_limit
        })
        response = Client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def start_chat(self, current_user, other_user):
       """Send a request to start a new chat."""
       Client.send_message({
            "action": "start_chat",
            "current_user": current_user,
            "other_user": other_user
        })
       response = Client.receive_message()
       return response.get("chat_id"), response.get("error_message", "")

    def get_users_to_display(
        self, current_user, search_pattern, current_page, users_per_page
    ):
        Client.send_message({
    "action": "get_all_users",
    "search_pattern": search_pattern,
    "page": current_page,
    "users_per_page": users_per_page
        })
        response = Client.receive_message()
        return response.get("users", []), response.get("error_message", "")

    def delete_account(self, current_user):
        del self.users[current_user]

        # Remove user from all chats

        # NOTE: (DOCS) This means, users who interacted with with curr user
        # will lose all chats/messages
        Client.send_message({
            "action": "delete_user",
            "username": current_user
        })
        response = Client.receive_message()
        return response.get("success"), response.get("error_message", "")

    def get_user_message_limit(self, current_user):
        Client.send_message({
            "action": "get_user_message_limit",
            "username": current_user
        })
        response = Client.receive_message()
        return response.get("message_limit"), response.get("error_message", "")
    
    def get_chats(self, user_id):
        """Request chat history for a user."""
        self.client.send_message({
            "action": "get_chats",
            "user_id": user_id
        })
        response = self.client.receive_message()
        if response.get("success"):
            # Convert the chats dictionary to a list of chat objects
            chats = [
                {"chat_id": chat_id, **chat_data}
                for chat_id, chat_data in response.get("chats", {}).items()
            ]
            return chats, response.get("error_message", "")
        else:
            return [], response.get("error_message", "Failed to fetch chats")
        
    def get_other_user_in_chat(self, chat_id, current_user):
        """Get the other user in the chat."""
        Client.send_message({
            "action": "get_other_user_in_chat",
            "chat_id": chat_id
        })
        response = Client.receive_message()
        return response.get("user", []), response.get("error_message", "")

    def get_messages(self, chat_id):
        """Get messages for a chat."""
        Client.send_message({
            "action": "get_messages",
            "chat_id": chat_id
        })
        response = Client.receive_message()
        return response.get("chats", []), response.get("error_message", "")
    
    def send_chat_message(self, chat_id, sender, content):
        """Send a message in a chat."""
        Client.send_message({
            "action": "send_chat_messages",
            "chat_id": chat_id
        })
        response = Client.receive_message()
        return response.get("chats", []), response.get("error_message", "")
    
    def get_unread_message_count(self, chat_id, current_user):
        """Count unread messages in a chat for a specific user."""
        chats, error = self.client.get_chats(current_user)
        if error:
            return 0, error

        for chat in chats.values():
            if chat["chat_id"] == chat_id:
                unread_count = sum(
                    1
                    for msg in chat["messages"]
                    if msg["sender"] != current_user and not msg["read"]
                )
                return unread_count, None

        return 0, "Chat not found"