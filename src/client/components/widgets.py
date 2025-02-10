"""Widget components for the chat application."""

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QCheckBox


class ChatWidget(QFrame):
    """A widget representing a chat in the list."""
    
    def __init__(self, username, unread_count=0, show_checkbox=False, parent=None):
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
    """A widget representing a chat message."""
    
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
