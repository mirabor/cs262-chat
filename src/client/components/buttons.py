"""Button components for the chat application."""

from PyQt6.QtWidgets import QPushButton


class DarkPushButton(QPushButton):
    """A styled dark push button."""
    
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
