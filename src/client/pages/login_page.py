"""Login page component for the chat application."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from PyQt6.QtCore import Qt
from components import DarkPushButton


class LoginPage(QWidget):
    """Login page widget that handles user authentication."""

    def __init__(self, parent=None):
        """Initialize the login page.
        
        Args:
            parent: The parent widget (ChatAppUI)
        """
        super().__init__(parent)
        self.main_window = parent
        self._setup_ui()

    def _setup_ui(self):
        """Set up the login page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("Login")
        title.setStyleSheet("font-size: 24px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username input
        username_label = QLabel("Username:")
        layout.addWidget(username_label)
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)

        # Password input
        password_label = QLabel("Password:")
        layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        # Login button
        login_btn = DarkPushButton("Login")
        login_btn.clicked.connect(self._handle_login)
        layout.addWidget(login_btn)

        # Sign up button
        signup_btn = DarkPushButton("Sign Up")
        signup_btn.clicked.connect(self.main_window.show_signup_page)
        layout.addWidget(signup_btn)

        layout.addStretch()

    def _handle_login(self):
        """Handle the login button click."""
        self.main_window.login(
            self.username_input.text(),
            self.password_input.text()
        )
