import json
import os
from datetime import datetime
from .utils import hash_password, verify_password
from fnmatch import fnmatch
from typing import List, Dict, Tuple, Optional, Any


class ChatAppLogic:
    def __init__(self):
        self.current_user = None
        self._init_data_store()

    def _init_data_store(self) -> None:
        """Core method to initialize and load data storage"""
        self._ensure_data_files_exist()
        self.load_data()

    def _ensure_data_files_exist(self) -> None:
        """Core method to ensure required data files exist"""
        for filename in ["users.json", "chats.json"]:
            if not os.path.exists(filename):
                with open(filename, "w") as f:
                    json.dump({}, f)

    def _core_data_operation(self, operation_type: str, data: Dict) -> None:
        """Core method to handle data operations

        Args:
            operation_type: Type of operation ('save' or 'load')
            data: Data to be saved/loaded
        """
        filename = f"{data['type']}.json"

        if operation_type == 'save':
            with open(filename, "w") as f:
                json.dump(data['content'], f)
        elif operation_type == 'load':
            with open(filename, "r") as f:
                return json.load(f)

    def _core_user_operation(self, operation_type: str, user_data: Dict) -> bool:
        """Core method to handle user operations

        Args:
            operation_type: Type of operation ('create', 'authenticate', 'delete')
            user_data: User-related data for the operation

        Returns:
            bool: Operation success status
        """
        if operation_type == 'create':
            if not all([user_data['username'], user_data['nickname'], user_data['password']]):
                return False
            if user_data['username'] in self.users:
                return False

            self.users[user_data['username']] = {
                "nickname": user_data['nickname'],
                "password": hash_password(user_data['password']),
                "message_limit": 6
            }
            self._core_data_operation('save', {'type': 'users', 'content': self.users})
            return True

        elif operation_type == 'authenticate':
            if user_data['username'] in self.users:
                stored_password = self.users[user_data['username']]["password"]
                if verify_password(user_data['password'], stored_password):
                    self.current_user = user_data['username']
                    return True
            return False

        elif operation_type == 'delete':
            username = user_data['username']
            if username in self.users:
                del self.users[username]
                self._delete_user_chats(username)
                self._core_data_operation('save', {'type': 'users', 'content': self.users})
                return True
            return False

    def _core_chat_operation(self, operation_type: str, chat_data: Dict) -> Any:
        """Core method to handle chat operations

        Args:
            operation_type: Type of operation ('create', 'delete', 'message')
            chat_data: Chat-related data for the operation

        Returns:
            Various types depending on operation
        """
        if operation_type == 'create':
            user1, user2 = sorted([chat_data['current_user'], chat_data['other_user']])
            chat_id = f"{user1}_{user2}"

            if chat_id not in self.chats:
                self.chats[chat_id] = {
                    "participants": [user1, user2],
                    "messages": []
                }
                self._core_data_operation('save', {'type': 'chats', 'content': self.chats})
            return chat_id

        elif operation_type == 'delete':
            if 'chat_ids' in chat_data:
                for chat_id in chat_data['chat_ids']:
                    if chat_id in self.chats:
                        del self.chats[chat_id]
            elif 'message_data' in chat_data:
                return self._delete_messages(
                    chat_data['message_data']['chat_id'],
                    chat_data['message_data']['indices'],
                    chat_data['message_data']['current_user']
                )
            self._core_data_operation('save', {'type': 'chats', 'content': self.chats})

        elif operation_type == 'message':
            chat_id = chat_data['chat_id']
            self.chats[chat_id]["messages"].append({
                "sender": chat_data['sender'],
                "content": chat_data['content'],
                "timestamp": datetime.now().isoformat(),
                "read": False
            })
            self._core_data_operation('save', {'type': 'chats', 'content': self.chats})

    def _delete_user_chats(self, username: str) -> None:
        """Helper method to delete all chats associated with a user"""
        for chat_id in list(self.chats.keys()):
            if username in self.chats[chat_id]["participants"]:
                del self.chats[chat_id]
        self._core_data_operation('save', {'type': 'chats', 'content': self.chats})

    def _delete_messages(self, chat_id: str, message_indices: List[int], current_user: str) -> Tuple[bool, str]:
        """Helper method to delete messages from a chat"""
        unauthorized_attempt = False

        for i in sorted(message_indices, reverse=True):
            if self.chats[chat_id]["messages"][i]["sender"] == current_user:
                del self.chats[chat_id]["messages"][i]
            else:
                unauthorized_attempt = True

        if unauthorized_attempt:
            return False, "You can only delete messages that you sent."
        return True, "Messages deleted successfully."

    # Original methods maintained for backward compatibility
    def delete_chats(self, chat_ids: List[str]) -> None:
        self._core_chat_operation('delete', {'chat_ids': chat_ids})

    def delete_messages(self, chat_id: str, message_indices: List[int], current_user: str) -> Tuple[bool, str]:
        return self._core_chat_operation('delete', {
            'message_data': {
                'chat_id': chat_id,
                'indices': message_indices,
                'current_user': current_user
            }
        })

    def send_message(self, chat_id: str, sender: str, content: str) -> None:
        self._core_chat_operation('message', {
            'chat_id': chat_id,
            'sender': sender,
            'content': content
        })

    def login(self, username: str, password: str) -> bool:
        return self._core_user_operation('authenticate', {
            'username': username,
            'password': password
        })

    def signup(self, username: str, nickname: str, password: str) -> bool:
        return self._core_user_operation('create', {
            'username': username,
            'nickname': nickname,
            'password': password
        })

    def save_settings(self, username: str, message_limit: int) -> None:
        if username in self.users:
            self.users[username]["message_limit"] = message_limit
            self._core_data_operation('save', {'type': 'users', 'content': self.users})

    def start_chat(self, current_user: str, other_user: str) -> str:
        return self._core_chat_operation('create', {
            'current_user': current_user,
            'other_user': other_user
        })

    def get_users_to_display(self, current_user: str, search_pattern: str,
                            current_page: int, users_per_page: int) -> List[str]:
        if not search_pattern:
            self.filtered_users = [
                username for username in self.users if username != current_user
            ]
        else:
            self.filtered_users = [
                username
                for username in self.users
                if username != current_user and fnmatch(username, f"*{search_pattern}*")
            ]

        start_index = current_page * users_per_page
        end_index = start_index + users_per_page
        return self.filtered_users[start_index:end_index]

    def load_data(self) -> None:
        self.users = self._core_data_operation('load', {'type': 'users'})
        self.chats = self._core_data_operation('load', {'type': 'chats'})

    def save_data(self) -> None:
        self._core_data_operation('save', {'type': 'users', 'content': self.users})
        self._core_data_operation('save', {'type': 'chats', 'content': self.chats})

    def delete_account(self, current_user: str) -> None:
        self._core_user_operation('delete', {'username': current_user})

    def get_user_message_limit(self, current_user: str) -> str:
        return str(self.users[current_user].get("message_limit", ""))