from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from ..components import DarkPushButton, MessageWidget


class ChatPage(QWidget):
    """Chat page widget that displays messages between users."""

    def __init__(self, parent=None, chat_id=None, other_user=None):
        """Initialize the chat page.

        Args:
            parent: The parent widget (ChatAppUI)
            chat_id: The ID of the chat to display (when coming from HomePage)
            other_user: The username of the other user (when coming from UserPage)
        """
        super().__init__(parent)
        self.main_window = parent
        self.chat_id = chat_id
        self.other_user = other_user
        self.message_widgets = []
        self._setup_ui()

    def _setup_ui(self):
        """Set up the chat page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Navigation
        self.main_window.create_navigation(layout, show_delete=True)

        # Header
        header_layout = QHBoxLayout()
        back_btn = DarkPushButton("Chat")
        back_btn.clicked.connect(self.main_window.show_home_page)
        header_layout.addWidget(back_btn)

        # Get other user's name from chat if not already provided
        if self.chat_id is not None and self.other_user is None:
            self.other_user = self.main_window.logic.get_other_user_in_chat(self.chat_id)
        
        # Make sure we have a valid other_user to display
        if self.other_user is None:
            QMessageBox.critical(self, "Error", "Could not determine chat participant")
            self.main_window.show_home_page()
            return
            
        chat_label = QLabel(f"Chat with {self.other_user}")
        chat_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(chat_label, alignment=Qt.AlignmentFlag.AlignCenter)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Delete button
        delete_btn = DarkPushButton("Delete Selected Messages")
        delete_btn.clicked.connect(self._delete_selected_messages)
        layout.addWidget(delete_btn)

        # Messages area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.messages_layout = QVBoxLayout(scroll_content)

        # Add spacer at the top to push messages to bottom
        self.messages_layout.addStretch(1)

        # Display messages
        self._display_messages()

        self.scroll_area.setWidget(scroll_content)
        layout.addWidget(self.scroll_area)

        # Scroll to bottom after a short delay to ensure layout is updated
        self.scroll_area.verticalScrollBar().rangeChanged.connect(
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            )
        )

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self._send_chat_message)  # Corrected
        input_layout.addWidget(self.message_input)
        layout.addLayout(input_layout)

    def _display_messages(self):
        """Display messages in the chat."""
        messages, error = self.main_window.logic.get_messages(self.chat_id, self.main_window.current_user)
        if error:
            QMessageBox.critical(self, "Error", f"Failed to fetch messages: {error}")
            return

        for message in messages:
            is_sender = message["sender"] == self.main_window.current_user
            msg_widget = MessageWidget(message["content"], is_sender)
            self.message_widgets.append(msg_widget)
            self.messages_layout.addWidget(msg_widget)

    def _delete_selected_messages(self):
        """Delete selected messages."""
        messages_to_delete = [
            i
            for i, msg_widget in enumerate(self.message_widgets)
            if msg_widget.checkbox and msg_widget.checkbox.isChecked()
        ]

        if not messages_to_delete:
            QMessageBox.warning(
                self, "No Selection", "No messages selected for deletion."
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete the selected messages?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            
            success, error = self.main_window.logic.delete_messages(
                self.chat_id, messages_to_delete, self.main_window.current_user
            )

            if not success:
                QMessageBox.critical(self, "Error", error)
                return

            for i in sorted(messages_to_delete, reverse=True):
                widget = self.message_widgets.pop(i)
                widget.setParent(None)

    def _send_chat_message(self):
        """Send a new message."""
        content = self.message_input.text().strip()
        if not content:
            return

        print(f"Sending message: {content} from {self.main_window.current_user} with chat id {self.chat_id}")

        success, error = self.main_window.logic.send_chat_message(self.chat_id, self.main_window.current_user, content)

        print(f"Success value is: {success}, error value is: {error}")
        if not success:
            print(f"Failed to send message: {error}")
            QMessageBox.critical(self, "Error", f"Failed to send message: {error}")
            return

        # Clear the input field after successful sending
        self.message_input.clear()

        # Display the new message in the UI
        msg_widget = MessageWidget(content, True)
        self.message_widgets.append(msg_widget)
        self.messages_layout.addWidget(msg_widget)

        # Scroll to bottom
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )