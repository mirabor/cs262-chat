"""Home page component for the chat application."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from components import ChatWidget


class HomePage(QWidget):
    """Home page widget that displays user's chats."""

    def __init__(self, parent=None):
        """Initialize the home page.
        
        Args:
            parent: The parent widget (ChatAppUI)
        """
        super().__init__(parent)
        self.main_window = parent
        self.chat_widgets = {}  # Track chat widgets
        self._setup_ui()

    def _setup_ui(self):
        """Set up the home page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Navigation
        self.main_window.create_navigation(layout, show_delete=False)

        # Welcome message
        welcome_label = QLabel(f"Welcome, {self.main_window.current_user}")
        welcome_label.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        layout.addWidget(welcome_label)

        # Scroll area for chats
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)

        # Display chats
        self._display_chats()

        self.scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def _display_chats(self):
        """Display user's chats in the scroll area."""
        current_user = self.main_window.current_user
        logic = self.main_window.logic

        for chat_id, chat_data in logic.chats.items():
            if current_user in chat_data["participants"]:
                # Get the other participant in the chat
                other_user = next(
                    p for p in chat_data["participants"] 
                    if p != current_user
                )

                # Count unread messages
                unread_count = sum(
                    1
                    for msg in chat_data["messages"]
                    if msg.get("sender") != current_user
                    and not msg.get("read", False)
                )

                # Create chat widget
                chat_widget = ChatWidget(other_user, unread_count, show_checkbox=False)
                chat_widget.mousePressEvent = (
                    lambda e, cid=chat_id: self.main_window.show_chat_page(cid)
                )
                self.scroll_layout.addWidget(chat_widget)

                # Store widget reference
                self.chat_widgets[chat_id] = chat_widget
