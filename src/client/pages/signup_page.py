"""Signup page component for the chat application."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from components import DarkPushButton


class SignupPage(QWidget):
    """Signup page widget that handles user registration."""

    def __init__(self, parent=None):
        """Initialize the signup page.
        
        Args:
            parent: The parent widget (ChatAppUI)
        """
        super().__init__(parent)
        self.main_window = parent
        self._setup_ui()

    def _setup_ui(self):
        """Set up the signup page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Sign Up")
        title.setStyleSheet("font-size: 24px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username input
        username_label = QLabel("Username:")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Nickname input
        nickname_label = QLabel("Nickname:")
        layout.addWidget(nickname_label)
        self.nickname_input = QLineEdit()
        layout.addWidget(self.nickname_input)

        # Password input
        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Sign up button
        signup_btn = DarkPushButton("Sign Up")
        signup_btn.clicked.connect(self._handle_signup)
        layout.addWidget(signup_btn)

        # Back button
        back_btn = DarkPushButton("Back")
        back_btn.clicked.connect(self.main_window.show_login_page)
        layout.addWidget(back_btn)

        layout.addStretch()

    def _handle_signup(self):
        """Handle the signup button click."""
        self.main_window.signup(
            self.username_input.text(),
            self.nickname_input.text(),
            self.password_input.text()
        )
