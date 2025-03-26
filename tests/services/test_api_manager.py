"""Test cases for the APIManager class."""

import pytest
from unittest.mock import patch, MagicMock

from src.services.api_manager import APIManager


@pytest.fixture
def api_manager():
    """Create an APIManager instance with a mocked db_manager."""
    with patch("src.services.db_manager.DBManager") as mock_db_manager_class:
        # Create mock instance
        mock_db_manager = MagicMock()
        mock_db_manager_class.return_value = mock_db_manager

        # Create APIManager with the mocked db_manager
        manager = APIManager(db_file="test.db")

        # Replace the real db_manager with our mock
        manager.db_manager = mock_db_manager

        yield manager


def test_signup(api_manager):
    """Test the signup method."""
    # Arrange
    api_manager.db_manager.add_user.return_value = {"success": True}
    input_data = {
        "username": "testuser",
        "nickname": "Test User",
        "password": "hashedpassword",
    }

    # Act
    result = api_manager.signup(input_data)

    # Assert
    assert result == {"success": True}
    api_manager.db_manager.add_user.assert_called_once_with(
        username="testuser", nickname="Test User", password="hashedpassword"
    )


def test_login(api_manager):
    """Test the login method."""
    # Arrange
    api_manager.db_manager.login.return_value = {
        "success": True,
        "user_id": 1,
        "nickname": "Test User",
    }
    login_data = {"username": "testuser", "password": "hashedpassword"}

    # Act
    result = api_manager.login(login_data)

    # Assert
    assert result == {"success": True, "user_id": 1, "nickname": "Test User"}
    api_manager.db_manager.login.assert_called_once_with(login_data)


def test_delete_user(api_manager):
    """Test the delete_user method."""
    # Arrange
    api_manager.db_manager.delete_user.return_value = {"success": True}
    user_id = "testuser"

    # Act
    result = api_manager.delete_user(user_id)

    # Assert
    assert result == {"success": True}
    api_manager.db_manager.delete_user.assert_called_once_with(user_id)


def test_get_chats(api_manager):
    """Test the get_chats method."""
    # Arrange
    api_manager.db_manager.get_chats.return_value = {
        "success": True,
        "chats": [{"id": 1, "name": "Chat 1"}],
    }
    user_id = "testuser"

    # Act
    result = api_manager.get_chats(user_id)

    # Assert
    assert result == {"success": True, "chats": [{"id": 1, "name": "Chat 1"}]}
    api_manager.db_manager.get_chats.assert_called_once_with(user_id)


def test_get_all_users(api_manager):
    """Test the get_all_users method."""
    # Arrange
    api_manager.db_manager.get_all_users.return_value = {
        "success": True,
        "users": [{"username": "user1"}, {"username": "user2"}],
    }
    exclude_username = "currentuser"

    # Act
    result = api_manager.get_all_users(exclude_username)

    # Assert
    assert result == {
        "success": True,
        "users": [{"username": "user1"}, {"username": "user2"}],
    }
    api_manager.db_manager.get_all_users.assert_called_once_with(exclude_username)


def test_update_view_limit(api_manager):
    """Test the update_view_limit method."""
    # Arrange
    api_manager.db_manager.update_view_limit.return_value = {"success": True}
    username = "testuser"
    new_limit = 10

    # Act
    result = api_manager.update_view_limit(username, new_limit)

    # Assert
    assert result == {"success": True}
    api_manager.db_manager.update_view_limit.assert_called_once_with(
        username, new_limit
    )


def test_get_user_message_limit(api_manager):
    """Test the get_user_message_limit method."""
    # Arrange
    api_manager.db_manager.get_user_message_limit.return_value = {
        "success": True,
        "limit": 10,
    }
    username = "testuser"

    # Act
    result = api_manager.get_user_message_limit(username)

    # Assert
    assert result == {"success": True, "limit": 10}
    api_manager.db_manager.get_user_message_limit.assert_called_once_with(username)


def test_save_settings(api_manager):
    """Test the save_settings method."""
    # Arrange
    api_manager.db_manager.save_settings.return_value = {"success": True}
    username = "testuser"
    message_limit = 10

    # Act
    result = api_manager.save_settings(username, message_limit)

    # Assert
    assert result == {"success": True}
    api_manager.db_manager.save_settings.assert_called_once_with(
        username, message_limit
    )


def test_start_chat(api_manager):
    """Test the start_chat method."""
    # Arrange
    api_manager.db_manager.start_chat.return_value = {"success": True, "chat_id": 1}
    current_user = "user1"
    other_user = "user2"

    # Act
    result = api_manager.start_chat(current_user, other_user)

    # Assert
    assert result == {"success": True, "chat_id": 1}
    api_manager.db_manager.start_chat.assert_called_once_with(current_user, other_user)


def test_delete_messages(api_manager):
    """Test the delete_messages method."""
    # Arrange
    api_manager.db_manager.delete_messages.return_value = {"success": True}
    chat_id = 1
    message_indices = [0, 1, 2]
    current_user = "testuser"

    # Act
    result = api_manager.delete_messages(chat_id, message_indices, current_user)

    # Assert
    assert result == {"success": True}
    api_manager.db_manager.delete_messages.assert_called_once_with(
        chat_id, message_indices, current_user
    )


def test_get_messages_valid_payload(api_manager):
    """Test the get_messages method with valid payload."""
    # Arrange
    api_manager.db_manager.get_messages.return_value = {
        "messages": [{"id": 1, "content": "Hello"}],
        "success": True,
    }
    payload = {"chat_id": 1, "current_user": "testuser"}

    # Act
    result = api_manager.get_messages(payload)

    # Assert
    assert result == {"messages": [{"id": 1, "content": "Hello"}], "success": True}
    api_manager.db_manager.get_messages.assert_called_once_with(1, "testuser")


def test_get_messages_invalid_payload_missing_chat_id(api_manager):
    """Test the get_messages method with invalid payload (missing chat_id)."""
    # Arrange
    payload = {"current_user": "testuser"}

    # Act
    result = api_manager.get_messages(payload)

    # Assert
    assert result == {"messages": [], "error_message": "Invalid payload."}
    api_manager.db_manager.get_messages.assert_not_called()


def test_get_messages_invalid_payload_missing_user(api_manager):
    """Test the get_messages method with invalid payload (missing current_user)."""
    # Arrange
    payload = {"chat_id": 1}

    # Act
    result = api_manager.get_messages(payload)

    # Assert
    assert result == {"messages": [], "error_message": "Invalid payload."}
    api_manager.db_manager.get_messages.assert_not_called()


def test_send_chat_message(api_manager):
    """Test the send_chat_message method."""
    # Arrange
    api_manager.db_manager.send_chat_message.return_value = {
        "success": True,
        "message_id": 1,
    }
    chat_id = 1
    sender = "sender"
    content = "Hello, world!"

    # Act
    result = api_manager.send_chat_message(chat_id, sender, content)

    # Assert
    assert result == {"success": True, "message_id": 1}
    api_manager.db_manager.send_chat_message.assert_called_once_with(
        chat_id, sender, content
    )


def test_get_users_to_display(api_manager):
    """Test the get_users_to_display method."""
    # Arrange
    api_manager.db_manager.get_users_to_display.return_value = {
        "success": True,
        "users": [{"username": "user1"}],
        "total_pages": 1,
    }
    exclude_username = "currentuser"
    search_pattern = "user"
    current_page = 1
    users_per_page = 10

    # Act
    result = api_manager.get_users_to_display(
        exclude_username, search_pattern, current_page, users_per_page
    )

    # Assert
    assert result == {
        "success": True,
        "users": [{"username": "user1"}],
        "total_pages": 1,
    }
    api_manager.db_manager.get_users_to_display.assert_called_once_with(
        exclude_username, search_pattern, current_page, users_per_page
    )
