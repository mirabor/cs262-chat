"""Users page component for the chat application."""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
)
from ..components import DarkPushButton, ChatWidget


class UsersPage(QWidget):
    """Users page widget that displays available users for chat."""

    def __init__(self, parent=None):
        """Initialize the users page.

        Args:
            parent: The parent widget (ChatAppUI)
        """
        super().__init__(parent)
        self.main_window = parent
        self.current_page = 0
        self.users_per_page = 10
        self._setup_ui()

    def _setup_ui(self):
        """Set up the users page UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Navigation
        self.main_window.create_navigation(layout, show_delete=False)

        # Title
        title = QLabel("Users")
        title.setStyleSheet("font-size: 24px;")
        layout.addWidget(title)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.textChanged.connect(self._update_users_display)
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

        layout.addLayout(pagination_layout)

        # Initialize display
        self._update_users_display()
    def _update_users_display(self):
        """Update the users display based on search and pagination."""
        # Clear current display
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
            else:
                self.scroll_layout.removeItem(item)

        # Get users to display
        search_pattern = self.search_input.text().strip()
        users_to_display, error = self.main_window.logic.get_users_to_display(
            self.main_window.current_user,
            search_pattern,
            self.current_page,
            self.users_per_page,
        )

        if error:
            print(f"Error fetching users: {error}")
            return

        # Store fetched users in filtered_users
        self.main_window.logic.filtered_users = users_to_display

        # Display users or "no users" message
        if not users_to_display:
            no_users_label = QLabel("No users found.")
            no_users_label.setStyleSheet("font-size: 18px; color: white;")
            self.scroll_layout.addWidget(no_users_label)
        else:
            for username in users_to_display:
                user_widget = ChatWidget(username)
                user_widget.mousePressEvent = (
                    lambda e, u=username: self.main_window.start_chat(u)
                )
                self.scroll_layout.addWidget(user_widget)

        self.scroll_layout.addStretch()
