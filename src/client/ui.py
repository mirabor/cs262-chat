import sys
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
from fnmatch import fnmatch
from utils import hash_password, verify_password
from logic import ChatAppLogic

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
    def __init__(self, username, unread_count=0, show_checkbox = False, parent=None):
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

        # Add checkbox only if show_checkbox is True
        if show_checkbox:
            self.checkbox = QCheckBox()
            self.checkbox.setStyleSheet("QCheckBox { color: white; }")
            layout.addWidget(self.checkbox)

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

        if is_sender:
            layout.addStretch()
            layout.addWidget(msg_label)
        else:
            layout.addWidget(msg_label)
            layout.addStretch()

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
        self.logic.load_data()       # Load data from logic class
        self.show_login_page()       # Show UI page, not from logic

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
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout, show_delete = False)

        welcome_label = QLabel(f"Welcome, {self.current_user}")
        welcome_label.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        layout.addWidget(welcome_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        # Initialize a dictionary to keep track of chat widgets
        self.chat_widgets = {}

        for chat_id, chat_data in self.logic.chats.items():
            if self.current_user in chat_data["participants"]:
                other_user = [p for p in chat_data["participants"] if p != self.current_user][0]

                unread_count = sum(
                    1 for msg in chat_data["messages"]
                    if msg.get("sender") != self.current_user and not msg.get("read", False)
                )

                chat_widget = ChatWidget(other_user, unread_count, show_checkbox = False)
                chat_widget.mousePressEvent = lambda e, cid=chat_id: self.show_chat_page(cid)
                self.scroll_layout.addWidget(chat_widget)

                # Store the widget in the dictionary
                self.chat_widgets[chat_id] = chat_widget

        self.scroll_layout.addStretch()
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
            p for p in self.logic.chats[chat_id]["participants"] if p != self.current_user
        ][0]
        chat_label = QLabel(f"Chat with {other_user}")
        chat_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(chat_label, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Delete button
        delete_btn = DarkPushButton("Delete Selected Messages")
        delete_btn.clicked.connect(lambda: self.delete_selected_messages(chat_id))
        layout.addWidget(delete_btn)

        # Messages area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.messages_layout = QVBoxLayout(scroll_content)  # Initialize self.messages_layout here

        # Mark messages as read
        for message in self.logic.chats[chat_id]["messages"]:
            if message["sender"] != self.current_user:
                message["read"] = True
        self.logic.save_data()

        # Initialize self.message_widgets as an empty list
        self.message_widgets = []

        # Display messages
        for message in self.logic.chats[chat_id]["messages"]:
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

    def show_users_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout, show_delete=False)

        title = QLabel("Users")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self.update_users_display)
        layout.addWidget(self.search_input)

        # Scroll area for users
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Pagination controls
        pagination_layout = QHBoxLayout()
        self.prev_btn = DarkPushButton("Previous")
        self.prev_btn.clicked.connect(self.show_previous_users)
        pagination_layout.addWidget(self.prev_btn)

        self.next_btn = DarkPushButton("Next")
        self.next_btn.clicked.connect(self.show_next_users)
        pagination_layout.addWidget(self.next_btn)

        layout.addLayout(pagination_layout)

        # Initialize pagination variables
        self.current_page = 0
        self.users_per_page = 10  # Number of users to display per page
        self.filtered_users = []  # List of users matching the search pattern

        # Update the display
        self.update_users_display()
   
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
    
    def show_settings_page(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        self.create_navigation(layout, show_delete= False)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        # Message limit setting
        limit_label = QLabel("Message view limit:")
        layout.addWidget(limit_label)
        self.limit_input = QLineEdit()
        self.limit_input.setText(
            str(self.logic.users[self.current_user].get("message_limit", ""))
        )
        layout.addWidget(self.limit_input)

        save_btn = DarkPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_settings(self.limit_input.text()))
        layout.addWidget(save_btn)

        delete_btn = DarkPushButton("Delete Account")
        delete_btn.clicked.connect(self.show_delete_confirmation)
        layout.addWidget(delete_btn)

        layout.addStretch()
    
    def show_delete_confirmation(self):
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self.logic.users[self.current_user]
            # Remove user from all chats
            for chat_id in list(self.logic.chats.keys()):
                if self.current_user in self.logic.chats[chat_id]["participants"]:
                    del self.logic.chats[chat_id]
            self.logic.save_data()
            self.current_user = None
            self.show_login_page()

    def show_previous_users(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_users_display()

    def show_next_users(self):
        if (self.current_page + 1) * self.users_per_page < len(self.filtered_users):
            self.current_page += 1
            self.update_users_display()

########### THESE ARE THE PARTS WHERE UI AND LOGIC ARE SPLIT   

    def delete_selected_chats(self):
        if not hasattr(self, 'chat_widgets') or not self.chat_widgets:
            QMessageBox.information(self, "No Selection", "No chats available to delete.")
            return
    
        chats_to_delete = [chat_id for chat_id, chat_widget in self.chat_widgets.items() if chat_widget.checkbox.isChecked()]

        if not chats_to_delete:
            QMessageBox.information(self, "No Selection", "No chats selected for deletion.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the selected chat(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.logic.delete_chats(chats_to_delete)  # Call business logic
            QMessageBox.information(self, "Success", "Selected chat(s) deleted successfully")
            self.show_home_page()

 
    def delete_selected_messages(self, chat_id):
        messages_to_delete = [i for i, msg_widget in enumerate(self.message_widgets) if msg_widget.checkbox.isChecked()]

        if not messages_to_delete:
            QMessageBox.warning(self, "No Selection", "No messages selected for deletion.")
            return

        success, message = self.logic.delete_messages(chat_id, messages_to_delete, self.current_user)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

        self.show_chat_page(chat_id)  # Refresh the chat page

    def send_message(self, chat_id, content):
        if content.strip():
            self.logic.send_message(chat_id, self.current_user, content)  # Call business logic
            self.message_input.clear()
            self.show_chat_page(chat_id)

    def login(self, username, password):
        if self.logic.login(username, password):  # Call business logic
            self.current_user = username
            self.show_home_page()
        else:
            QMessageBox.critical(self, "Error", "Invalid username or password")

    def signup(self, username, nickname, password):
        if self.logic.signup(username, nickname, password):  # Call business logic
            QMessageBox.information(self, "Success", "Account created successfully")
            self.show_login_page()
        else:
            QMessageBox.critical(self, "Error", "Username already taken or invalid input")

    def save_settings(self, message_limit):
        try:
            limit = int(message_limit)
            self.logic.save_settings(self.current_user, limit)  # Call business logic
            QMessageBox.information(self, "Success", "Settings saved")
            self.show_home_page()
        except ValueError:
            QMessageBox.critical(self, "Error", "Invalid message limit")

    def start_chat(self, other_user):
        if not self.current_user:
            QMessageBox.critical(self, "Error", "Please login first")
            return
        chat_id = self.logic.start_chat(self, other_user)  # Call business logic
        self.show_chat_page(chat_id)

    def update_users_display(self):

        # Clear the current display (UI task)
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
            else:
                self.scroll_layout.removeItem(item)

        # Get users to display from the business logic
        search_pattern = self.search_input.text().strip()
        users_to_display = self.logic.get_users_to_display(
            self.current_user, search_pattern, self.current_page, self.users_per_page
        )

        if not users_to_display:
            no_users_label = QLabel("No users found.")
            no_users_label.setStyleSheet("font-size: 18px; color: white;")
            self.scroll_layout.addWidget(no_users_label)

        # Display the users (UI task)
        for username in users_to_display:
            user_widget = ChatWidget(username)
            user_widget.mousePressEvent = lambda e, u=username: self.start_chat(u)
            self.scroll_layout.addWidget(user_widget)

        self.scroll_layout.addStretch()

        # Update pagination button states (UI task)
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(
            (self.current_page + 1) * self.users_per_page < len(self.logic.filtered_users)
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatAppUI()
    window.show()
    sys.exit(app.exec())
    def on_login_clicked(self):
        username = self.username_input.text()
        password = self.password_input.text()
        # This will be handled by the logic layer
        pass

    def on_signup_clicked(self):
        username = self.username_input.text()
        nickname = self.nickname_input.text()
        password = self.password_input.text()
        # This will be handled by the logic layer
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatAppUI()
    window.show()
    sys.exit(app.exec())