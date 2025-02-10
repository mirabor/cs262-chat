from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from logic import ChatAppLogic
from components import DarkPushButton, ChatWidget, MessageWidget


class ChatAppUI(QMainWindow):
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
        self.logic = ChatAppLogic()  # Instantiate ChatAppLogic
        self.logic.load_data()  # Load data from logic class
        self.show_login_page()  # Show UI page, not from logic

    def create_navigation(self, container, show_delete=False):
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)

        home_btn = DarkPushButton("Home")
        home_btn.clicked.connect(self.show_home_page)
        nav_layout.addWidget(home_btn)

        separator1 = QLabel("|")
        separator1.setStyleSheet("color: white; font-size: 20px;")
        nav_layout.addWidget(separator1)

        users_btn = DarkPushButton("Users")
        users_btn.clicked.connect(self.show_users_page)
        nav_layout.addWidget(users_btn)

        separator2 = QLabel("|")
        separator2.setStyleSheet("color: white; font-size: 20px;")
        nav_layout.addWidget(separator2)

        settings_btn = DarkPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings_page)
        nav_layout.addWidget(settings_btn)

        # Add the "Delete Selected Chat(s)" button only if show_delete is True
        if show_delete:
            delete_chat_btn = DarkPushButton("Delete Chat(s)")
            delete_chat_btn.clicked.connect(self.delete_selected_chats)
            nav_layout.addWidget(delete_chat_btn)

        nav_layout.addStretch()
        container.addLayout(nav_layout)

    def show_home_page(self):
        from pages.home_page import HomePage
        home_page = HomePage(self)
        self.setCentralWidget(home_page)

    def show_chat_page(self, chat_id):
        from pages.chat_page import ChatPage
        chat_page = ChatPage(self, chat_id)
        self.setCentralWidget(chat_page)

    def show_login_page(self):
        from pages.login_page import LoginPage
        login_page = LoginPage(self)
        self.setCentralWidget(login_page)

    def show_users_page(self):
        from pages.users_page import UsersPage
        users_page = UsersPage(self)
        self.setCentralWidget(users_page)

    def show_signup_page(self):
        from pages.signup_page import SignupPage
        signup_page = SignupPage(self)
        self.setCentralWidget(signup_page)

    def show_settings_page(self):
        from pages.settings_page import SettingsPage
        settings_page = SettingsPage(self)
        self.setCentralWidget(settings_page)

    def show_delete_confirmation(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logic.delete_account(self.current_user)
            self.current_user = None
            self.show_login_page()

    def delete_selected_messages(self, chat_id):
        messages_to_delete = [
            i
            for i, msg_widget in enumerate(self.message_widgets)
            if msg_widget.checkbox.isChecked()
        ]

        if not messages_to_delete:
            QMessageBox.warning(
                self, "No Selection", "No messages selected for deletion."
            )
            return

        success, message = self.logic.delete_messages(
            chat_id, messages_to_delete, self.current_user
        )

        if not success:
            QMessageBox.critical(self, "Error: ", message)

        self.show_chat_page(chat_id)  # Refresh the chat page

    def send_message(self, chat_id, content):
        if content.strip():
            self.logic.send_message(
                chat_id, self.current_user, content
            )  # Call business logic
            self.show_chat_page(chat_id)

    def login(self, username, password):
        if self.logic.login(username, password):  # Call business logic
            # TODO: have the current user set in the logic, not in the UI
            self.current_user = username
            self.show_home_page()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password")

    def signup(self, username, nickname, password):
        if self.logic.signup(username, nickname, password):  # Call business logic
            QMessageBox.information(self, "Success", "Account created successfully")
            self.show_login_page()
        else:
            QMessageBox.critical(
                self, "Error", "Username already taken or invalid input"
            )

    def save_settings(self, message_limit):
        try:
            limit = int(message_limit)
            self.logic.save_settings(self.current_user, limit)
            QMessageBox.information(self, "Success", "Settings saved")
            self.show_home_page()
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid message limit")

    def start_chat(self, other_user):
        if not self.current_user:
            QMessageBox.critical(self, "Error", "Please login first")
            return
        chat_id = self.logic.start_chat(self.current_user, other_user)  # Call business logic
        self.show_chat_page(chat_id)


