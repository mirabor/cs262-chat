import json
import os
import time
from typing import Dict, Any
from threading import Lock
from enum import Enum
import threading
from PyQt6.QtCore import QObject, pyqtSignal


class UpdateType(Enum):
    NEW_MESSAGE = "new_message"
    USER_UPDATE = "user_update"
    CHAT_UPDATE = "chat_update"


class StateManager(QObject):
    # Define signals for different update types
    message_update = pyqtSignal(dict)
    user_update = pyqtSignal(dict)
    chat_update = pyqtSignal(dict)

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateManager, cls).__new__(cls)
                cls._instance.__initialized = False
            return cls._instance

    def __init__(self):
        if self.__initialized:
            return
        super().__init__()
        self.__initialized = True

        # File paths
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.chats_file = os.path.join(self.base_path, "chats.json")
        self.users_file = os.path.join(self.base_path, "users.json")

        # Track file states
        self._last_chats_mtime = 0
        self._last_users_mtime = 0
        self._cached_chats = {}
        self._cached_users = {}
        self._last_chats_size = 0
        self._last_users_size = 0

        # Initial load of data
        self._load_initial_state()

        # Start file monitoring
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_files, daemon=True)
        self._monitor_thread.start()

    def _load_json_file(self, filepath: str) -> Dict:
        try:
            with open(filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading {filepath}: {e}")
            return {}

    def _load_initial_state(self):
        """Load initial state of files"""
        try:
            self._cached_chats = self._load_json_file(self.chats_file)
            self._cached_users = self._load_json_file(self.users_file)
            self._last_chats_mtime = os.path.getmtime(self.chats_file)
            self._last_users_mtime = os.path.getmtime(self.users_file)
            self._last_chats_size = os.path.getsize(self.chats_file)
            self._last_users_size = os.path.getsize(self.users_file)
        except Exception as e:
            print(f"Error loading initial state: {e}")

    def _check_chats_updates(self):
        try:
            # Check both mtime and size
            current_mtime = os.path.getmtime(self.chats_file)
            current_size = os.path.getsize(self.chats_file)

            if current_mtime > self._last_chats_mtime or current_size != self._last_chats_size:
                new_chats = self._load_json_file(self.chats_file)
                if new_chats:  # Only process if file load was successful
                    # Compare with cached chats to find updates
                    for chat_id, chat_data in new_chats.items():
                        if chat_id not in self._cached_chats:
                            # New chat
                            self.chat_update.emit(
                                {"chat_id": chat_id, "action": "new", **chat_data}
                            )
                        else:
                            old_messages = self._cached_chats[chat_id].get("messages", [])
                            new_messages = chat_data.get("messages", [])
                            if len(new_messages) > len(old_messages):
                                # New messages
                                for msg in new_messages[len(old_messages) :]:
                                    self.message_update.emit({"chat_id": chat_id, **msg})
                    
                    # Update cached state after processing
                    self._cached_chats = new_chats
                    self._last_chats_mtime = current_mtime
                    self._last_chats_size = current_size
        except Exception as e:
            print(f"Error checking chats updates: {e}")

    def _check_users_updates(self):
        try:
            # Check both mtime and size
            current_mtime = os.path.getmtime(self.users_file)
            current_size = os.path.getsize(self.users_file)

            if current_mtime > self._last_users_mtime or current_size != self._last_users_size:
                new_users = self._load_json_file(self.users_file)
                if new_users:  # Only process if file load was successful
                    # Compare with cached users to find updates
                    for username, user_data in new_users.items():
                        if username not in self._cached_users:
                            # New user
                            self.user_update.emit(
                                {"username": username, "action": "new", **user_data}
                            )
                        elif user_data != self._cached_users[username]:
                            # User data updated
                            self.user_update.emit(
                                {"username": username, "action": "update", **user_data}
                            )
                    
                    # Update cached state after processing
                    self._cached_users = new_users
                    self._last_users_mtime = current_mtime
                    self._last_users_size = current_size
        except Exception as e:
            print(f"Error checking users updates: {e}")

    def _monitor_files(self):
        """Monitor JSON files for changes"""
        while self._running:
            try:
                self._check_chats_updates()
                self._check_users_updates()
            except Exception as e:
                print(f"Error in file monitoring: {e}")
            time.sleep(0.1)  # Check more frequently

    def stop(self):
        """Stop the monitoring thread"""
        self._running = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join()
