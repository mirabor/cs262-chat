import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QCheckBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPalette, QColor


class DarkPushButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """
        )


class ChatWidget(QFrame):
    def __init__(self, username, unread_count=0, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #1e1e1e;
                color: white;
                padding: 10px;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        username_label = QLabel(username)
        username_label.setStyleSheet("font-size: 18px; color: white;")
        layout.addWidget(username_label)

        layout.addStretch()

        if unread_count > 0:
            unread_label = QLabel(f"[{unread_count} unreads]")
            unread_label.setStyleSheet("font-size: 16px; color: white;")
            layout.addWidget(unread_label)


class MessageWidget(QFrame):
    def __init__(self, message, is_sender, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            """
            QFrame {
                background-color: #1e1e1e;
                color: white;
                padding: 5px;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("QCheckBox { color: white; }")
        layout.addWidget(self.checkbox)

        if not is_sender:
            layout.addStretch()

        msg_label = QLabel(message)
        msg_label.setStyleSheet(
            """
            QLabel {
                background-color: #333333;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
        """
        )
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)

        if is_sender:
            layout.addStretch()

        if is_sender:
            layout.addStretch()


class ChatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Application")
        self.setGeometry(100, 100, 800, 600)

        # Set dark theme
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #333333;
                color: white;
                border: none;
                padding: 8px;
                font-size: 14px;
            }
        """
        )

        self.current_user = None
        self.load_data()
        self.show_login_page()

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

    def create_navigation(self, container):
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)

        home_btn = DarkPushButton("Home")
        home_btn.clicked.connect(self.show_home_page)
        nav_layout.addWidget(home_btn)

        separator1 = QLabel("|")
        separator1.setStyleSheet("color: white; font-size: 20px;")
        nav_layout.addWidget(separator1)

        users_btn = DarkPushButton("users")
        users_btn.clicked.connect(self.show_users_page)
        nav_layout.addWidget(users_btn)

        separator2 = QLabel("|")
        separator2.setStyleSheet("color: white; font-size: 20px;")
        nav_layout.addWidget(separator2)

        settings_btn = DarkPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings_page)
        nav_layout.addWidget(settings_btn)

        nav_layout.addStretch()
        container.addLayout(nav_layout)

    def show_home_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout)

        welcome_label = QLabel(f"Welcome, {self.current_user}")
        welcome_label.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        layout.addWidget(welcome_label)

        # Chat list with unread counts
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for chat_id, chat_data in self.chats.items():
            if self.current_user in chat_data["participants"]:
                other_user = [
                    p for p in chat_data["participants"] if p != self.current_user
                ][0]

                unread_count = sum(
                    1
                    for msg in chat_data["messages"]
                    if msg.get("sender") != self.current_user
                    and not msg.get("read", False)
                )

                chat_widget = ChatWidget(other_user, unread_count)
                chat_widget.mousePressEvent = (
                    lambda e, cid=chat_id: self.show_chat_page(cid)
                )
                scroll_layout.addWidget(chat_widget)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    
    def show_chat_page(self, chat_id):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        back_btn = DarkPushButton("Home")
        back_btn.clicked.connect(self.show_home_page)
        header_layout.addWidget(back_btn)

        other_user = [
            p for p in self.chats[chat_id]["participants"] if p != self.current_user
        ][0]
        chat_label = QLabel(f"Chat with {other_user}")
        chat_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(chat_label, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Messages area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.messages_layout = QVBoxLayout(scroll_content)  # Initialize self.messages_layout here

        # Mark messages as read
        for message in self.chats[chat_id]["messages"]:
            if message["sender"] != self.current_user:
                message["read"] = True
        self.save_data()

        # Initialize self.message_widgets as an empty list
        self.message_widgets = []

        # Display messages
        for message in self.chats[chat_id]["messages"]:
            is_sender = message["sender"] == self.current_user
            msg_widget = MessageWidget(message["content"], is_sender)
            self.message_widgets.append(msg_widget)  # Add message widget to the list
            self.messages_layout.addWidget(msg_widget)  # Add message widget to the layout

        self.messages_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(
            lambda: self.send_message(chat_id, self.message_input.text())
        )
        input_layout.addWidget(self.message_input)
        layout.addLayout(input_layout)

        # Delete button
        delete_btn = DarkPushButton("Delete Selected Messages")
        delete_btn.clicked.connect(lambda: self.delete_selected_messages(chat_id))
        layout.addWidget(delete_btn)

    def delete_selected_messages(self, chat_id):
        messages_to_delete = []
        for i, msg_widget in enumerate(self.message_widgets):
            if msg_widget.checkbox.isChecked():
                # Check if the current user is the sender of the message
                if self.chats[chat_id]["messages"][i]["sender"] == self.current_user:
                    messages_to_delete.append(i)
                else:
                    QMessageBox.warning(
                        self,
                        "Cannot Delete",
                        "You can only delete messages that you sent.",
                    )

        # Remove messages in reverse order to avoid index issues
        for i in sorted(messages_to_delete, reverse=True):
            del self.chats[chat_id]["messages"][i]

        self.save_data()
        self.show_chat_page(chat_id)  # Refresh the chat page

    def send_message(self, chat_id, content):
        if content.strip():
            self.chats[chat_id]["messages"].append(
                {
                    "sender": self.current_user,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                    "read": False,
                }
            )
            self.save_data()
            self.message_input.clear()
            self.show_chat_page(chat_id)

    def show_login_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Login")
        title.setStyleSheet("font-size: 24px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        username_label = QLabel("Username:")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        login_btn = DarkPushButton("Login")
        login_btn.clicked.connect(
            lambda: self.login(self.username_input.text(), self.password_input.text())
        )
        layout.addWidget(login_btn)

        signup_btn = DarkPushButton("Sign Up")
        signup_btn.clicked.connect(self.show_signup_page)
        layout.addWidget(signup_btn)

        layout.addStretch()

    def login(self, username, password):
        if username in self.users and self.users[username]["password"] == password:
            self.current_user = username
            self.show_home_page()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password")

    def show_signup_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Sign Up")
        title.setStyleSheet("font-size: 24px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        username_label = QLabel("Username:")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        nickname_label = QLabel("Nickname:")
        layout.addWidget(nickname_label)
        self.nickname_input = QLineEdit()
        layout.addWidget(self.nickname_input)

        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        signup_btn = DarkPushButton("Sign Up")
        signup_btn.clicked.connect(
            lambda: self.signup(
                self.username_input.text(),
                self.nickname_input.text(),
                self.password_input.text(),
            )
        )
        layout.addWidget(signup_btn)

        back_btn = DarkPushButton("Back")
        back_btn.clicked.connect(self.show_login_page)
        layout.addWidget(back_btn)

        layout.addStretch()

    def signup(self, username, nickname, password):
        if not username or not nickname or not password:
            QMessageBox.critical(self, "Error", "All fields are required")
            return

        if username in self.users:
            QMessageBox.critical(self, "Error", "Username already taken")
            return

        self.users[username] = {
            "nickname": nickname,
            "password": password,
            "message_limit": 6,
        }
        self.save_data()
        QMessageBox.information(self, "Success", "Account created successfully")
        self.show_login_page()

    def show_users_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout)

        title = QLabel("Users")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for username in self.users:
            if username != self.current_user:
                user_widget = ChatWidget(username)
                user_widget.mousePressEvent = lambda e, u=username: self.start_chat(u)
                scroll_layout.addWidget(user_widget)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def show_settings_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        # Message limit setting
        limit_label = QLabel("Message view limit:")
        layout.addWidget(limit_label)
        self.limit_input = QLineEdit()
        self.limit_input.setText(
            str(self.users[self.current_user].get("message_limit", ""))
        )
        layout.addWidget(self.limit_input)

        save_btn = DarkPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_settings(self.limit_input.text()))
        layout.addWidget(save_btn)

        delete_btn = DarkPushButton("Delete Account")
        delete_btn.clicked.connect(self.show_delete_confirmation)
        layout.addWidget(delete_btn)

        layout.addStretch()

    def save_settings(self, message_limit):
        try:
            limit = int(message_limit)
            self.users[self.current_user]["message_limit"] = limit
            self.save_data()
            QMessageBox.information(self, "Success", "Settings saved")
            self.show_home_page()
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid message limit")

    def show_delete_confirmation(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.users[self.current_user]
            # Remove user from all chats
            for chat_id in list(self.chats.keys()):
                if self.current_user in self.chats[chat_id]["participants"]:
                    del self.chats[chat_id]
            self.save_data()
            self.current_user = None
            self.show_login_page()

    def start_chat(self, other_user):
        if not self.current_user:
            QMessageBox.critical(self, "Error", "Please login first")
            return

        chat_id = (
            f"{min(self.current_user, other_user)}_{max(self.current_user, other_user)}"
        )

        if chat_id not in self.chats:
            self.chats[chat_id] = {
                "participants": [self.current_user, other_user],
                "messages": [],
            }
            self.save_data()

        self.show_chat_page(chat_id)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec())
