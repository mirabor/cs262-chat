from PyQt6.QtWidgets import (
    QMainWindow,
    QHBoxLayout,
    QLabel,
    QMessageBox,
)

from .client import Client
from .components.buttons import DarkPushButton
from .pages import (
    HomePage,
    ChatPage,
    LoginPage,
    UsersPage,
    SignupPage,
    SettingsPage,
)

from .logic import ChatAppLogic


class ChatAppUI(QMainWindow):
    def __init__(self, client=None, rpc_logic=None):
        """
        Initialize the ChatAppUI class.

        Args:
            client: An instance of the Client class (socket-based client)
            rpc_logic: An instance of the RpcLogic class (RPC-based client)

        Note:
            We only kept client just for backward compatibility from previous version.
            Therefore, this expect at least one of client or rpc_logic to be provided.
        """
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

        # Initialize logic
        if client is None and rpc_logic is None:
            raise ValueError("Either client or rpc_logic must be provided.")
        if client is not None:
            self.logic = ChatAppLogic(client)
        else:
            self.logic = rpc_logic

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
        # if show_delete:
        #     delete_chat_btn = DarkPushButton("Delete Chat(s)")
        #     delete_chat_btn.clicked.connect(self.logic.delete_selected_chats)
        #     nav_layout.addWidget(delete_chat_btn)

        nav_layout.addStretch()

        # Add logout button
        logout_btn = DarkPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        nav_layout.addWidget(logout_btn)

        container.addLayout(nav_layout)

    def show_home_page(self):
        home_page = HomePage(self)
        self.setCentralWidget(home_page)

    def show_chat_page(self, chat_id=None, other_user=None):
        chat_page = ChatPage(self, chat_id, other_user)
        self.setCentralWidget(chat_page)

    def show_login_page(self):
        login_page = LoginPage(self)
        self.setCentralWidget(login_page)

    def show_users_page(self):
        users_page = UsersPage(self)
        self.setCentralWidget(users_page)

    def show_signup_page(self):
        signup_page = SignupPage(self)
        self.setCentralWidget(signup_page)

    def logout(self):
        # Clear current user
        self.current_user = None
        # Show login page
        self.show_login_page()
        # Show logout message
        QMessageBox.information(self, "Logged Out", "You have been successfully logged out.")

    def show_settings_page(self):
        settings_page = SettingsPage(self)
        self.setCentralWidget(settings_page)

    def login(self, username, password):
        try:
            # if condition login returns a tuple, unpack and process
            success, error_message = self.logic.login(username, password)
            
            if success:  # Call business logic
                # TODO: have the current user set in the logic, not in the UI
                self.current_user = username
                self.show_home_page()
            else:
                QMessageBox.critical(self, "Invalid login", error_message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def signup(self, username, nickname, password):
        try:
            success, error_message = self.logic.signup(username, nickname, password)
            if success:
                QMessageBox.information(self, "Success", "Account created successfully")
                self.show_login_page()
            else:
                QMessageBox.critical(self, "Username already taken or invalid input", error_message)
        except Exception as e:
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def save_settings(self, message_limit):

        try:
            limit = int(message_limit)
            if limit < 1:
                QMessageBox.critical(self, "Error", "Message limit must be at least 1")
                return
            self.logic.save_settings(self.current_user, limit)
            
            QMessageBox.information(self, "Success", "Settings saved")
            self.show_home_page()
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid message limit")

    def start_chat(self, other_user):
        try:
            if not self.current_user:
                QMessageBox.critical(self, "Error", "Please login first")
                return
            
            # Attempt to create a new chat or get an existing chat ID
            chat_id, error = self.logic.start_chat(self.current_user, other_user)
            
            if error:
                QMessageBox.critical(self, "Error", error)
                # Still show chat page with other_user even if chat creation failed
                self.show_chat_page(other_user=other_user)
            else:
                # Show chat page with the new chat_id
                self.show_chat_page(chat_id=chat_id, other_user=other_user)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")