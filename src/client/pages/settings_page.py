"""Settings page component for the chat application."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QMessageBox
from ..components import DarkPushButton


class SettingsPage(QWidget):
    """Settings page widget that handles user preferences."""

    def __init__(self, parent=None):
        """Initialize the settings page.

        Args:
            parent: The parent widget (ChatAppUI)
        """
        super().__init__(parent)
        self.main_window = parent
        self._setup_ui()

    def _setup_ui(self):
        """Set up the settings page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Navigation
        self.main_window.create_navigation(layout, show_delete=False)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        # Message limit setting
        limit_label = QLabel("Message view limit:")
        layout.addWidget(limit_label)
        self.limit_input = QLineEdit()
        # Unpack the message limit and error message
        message_limit, error_message = self.main_window.logic.get_user_message_limit(self.main_window.current_user)

        # Check for errors before setting the text
        if error_message:
            QMessageBox.critical(self, "Error", f"Failed to fetch message limit: {error_message}")
            self.limit_input.setText("")  # Default to an empty string if there's an error
        else:
            self.limit_input.setText(str(message_limit))  # Convert message_limit to string
        layout.addWidget(self.limit_input)

        # Save button
        save_btn = DarkPushButton("Save")
        save_btn.clicked.connect(self._handle_save)
        layout.addWidget(save_btn)

        # Delete account button
        delete_btn = DarkPushButton("Delete Account")
        delete_btn.clicked.connect(self._show_delete_confirmation)
        layout.addWidget(delete_btn)

        layout.addStretch()

    def _handle_save(self):
        """Handle the save button click."""
        if not self.limit_input.text().isdigit():
            QMessageBox.critical(self, "Error", "Message limit must be a number.")
            return
        if int(self.limit_input.text()) < 1:
            QMessageBox.critical(self, "Error", "Message limit must be at least 1.")
            return
        print(f"Saving settings for {self.main_window.current_user} offset: {self.limit_input.text()}")
        success, error_message = self.main_window.logic.save_settings(self.main_window.current_user, self.limit_input.text())
        if success:
            # Refresh the UI to display the updated value
            self.update_ui_with_current_settings()
        else:
            print(f"Error saving settings: {error_message}")

    def update_ui_with_current_settings(self):
        # Fetch the updated message limit and update the UI
        message_limit, error_message = self.main_window.logic.get_user_message_limit(self.main_window.current_user)
        if error_message:
            print(f"Error fetching message limit: {error_message}")
        else:
            self.limit_input.setText(str(message_limit))

    def _show_delete_confirmation(self):
        """Show confirmation dialog for account deletion."""
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete your account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.main_window.logic.delete_account(self.main_window.current_user)
            self.main_window.current_user = None
            self.main_window.show_login_page()
