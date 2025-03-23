"""Test cases for the API module."""

import pytest
from unittest.mock import patch, MagicMock

from src.chatservice import api

@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    with patch('src.chatservice.api.db_manager') as mock:
        yield mock

def test_signup(mock_db_manager):
    """Test the signup function."""
    # Arrange
    mock_db_manager.add_user.return_value = {"success": True}
    input_data = {
        "username": "testuser",
        "nickname": "Test User",
        "password": "hashedpassword"
    }
    
    # Act
    result = api.signup(input_data)
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.add_user.assert_called_once_with(
        username="testuser",
        nickname="Test User",
        password="hashedpassword"
    )

def test_login(mock_db_manager):
    """Test the login function."""
    # Arrange
    mock_db_manager.login.return_value = {
        "success": True,
        "user_id": 1,
        "nickname": "Test User"
    }
    login_data = {
        "username": "testuser",
        "password": "hashedpassword"
    }
    
    # Act
    result = api.login(login_data)
    
    # Assert
    assert result == {
        "success": True,
        "user_id": 1,
        "nickname": "Test User"
    }
    mock_db_manager.login.assert_called_once_with(login_data)

def test_delete_user(mock_db_manager):
    """Test the delete_user function."""
    # Arrange
    mock_db_manager.delete_user.return_value = {"success": True}
    
    # Act
    result = api.delete_user("testuser")
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.delete_user.assert_called_once_with("testuser")

def test_get_chats(mock_db_manager):
    """Test the get_chats function."""
    # Arrange
    mock_db_manager.get_chats.return_value = {
        "success": True,
        "chats": [{"id": 1, "name": "Chat 1"}]
    }
    
    # Act
    result = api.get_chats("testuser")
    
    # Assert
    assert result == {
        "success": True,
        "chats": [{"id": 1, "name": "Chat 1"}]
    }
    mock_db_manager.get_chats.assert_called_once_with("testuser")

def test_get_all_users(mock_db_manager):
    """Test the get_all_users function."""
    # Arrange
    mock_db_manager.get_all_users.return_value = {
        "success": True,
        "users": [{"username": "user1"}, {"username": "user2"}]
    }
    
    # Act
    result = api.get_all_users("currentuser")
    
    # Assert
    assert result == {
        "success": True,
        "users": [{"username": "user1"}, {"username": "user2"}]
    }
    mock_db_manager.get_all_users.assert_called_once_with("currentuser")

def test_update_view_limit(mock_db_manager):
    """Test the update_view_limit function."""
    # Arrange
    mock_db_manager.update_view_limit.return_value = {"success": True}
    
    # Act
    result = api.update_view_limit("testuser", 10)
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.update_view_limit.assert_called_once_with("testuser", 10)

def test_get_user_message_limit(mock_db_manager):
    """Test the get_user_message_limit function."""
    # Arrange
    mock_db_manager.get_user_message_limit.return_value = {
        "success": True,
        "limit": 10
    }
    
    # Act
    result = api.get_user_message_limit("testuser")
    
    # Assert
    assert result == {
        "success": True,
        "limit": 10
    }
    mock_db_manager.get_user_message_limit.assert_called_once_with("testuser")

def test_save_settings(mock_db_manager):
    """Test the save_settings function."""
    # Arrange
    mock_db_manager.save_settings.return_value = {"success": True}
    
    # Act
    result = api.save_settings("testuser", 10)
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.save_settings.assert_called_once_with("testuser", 10)

def test_start_chat(mock_db_manager):
    """Test the start_chat function."""
    # Arrange
    mock_db_manager.start_chat.return_value = {
        "success": True,
        "chat_id": 1
    }
    
    # Act
    result = api.start_chat("user1", "user2")
    
    # Assert
    assert result == {
        "success": True,
        "chat_id": 1
    }
    mock_db_manager.start_chat.assert_called_once_with("user1", "user2")

def test_delete_chats(mock_db_manager):
    """Test the delete_chats function."""
    # Arrange
    mock_db_manager.delete_chats.return_value = {"success": True}
    chat_ids = [1, 2, 3]
    
    # Act
    result = api.delete_chats(chat_ids)
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.delete_chats.assert_called_once_with(chat_ids)

def test_delete_messages(mock_db_manager):
    """Test the delete_messages function."""
    # Arrange
    mock_db_manager.delete_messages.return_value = {"success": True}
    
    # Act
    result = api.delete_messages(1, [0, 1, 2], "testuser")
    
    # Assert
    assert result == {"success": True}
    mock_db_manager.delete_messages.assert_called_once_with(1, [0, 1, 2], "testuser")

def get_messages(payload):
    """Get messages for a chat."""
    if not isinstance(payload, dict):
        print(f"DEBUG: Get messages in api.py: payload {payload} is invalid")
        return {"messages": [], "error_message": "Invalid payload."}
    
    required_keys = {"chat_id", "username"}
    if not required_keys.issubset(payload.keys()):
        print(f"DEBUG: Get messages in api.py: payload {payload} is invalid")
        return {"messages": [], "error_message": "Invalid payload."}
    
    return db_manager.get_messages(payload["chat_id"], payload["username"])

def test_send_chat_message(mock_db_manager):
    """Test the send_chat_message function."""
    # Arrange
    mock_db_manager.send_chat_message.return_value = {
        "success": True,
        "message_id": 1
    }
    
    # Act
    result = api.send_chat_message(1, "sender", "Hello, world!")
    
    # Assert
    assert result == {
        "success": True,
        "message_id": 1
    }
    mock_db_manager.send_chat_message.assert_called_once_with(1, "sender", "Hello, world!")

def test_get_users_to_display(mock_db_manager):
    """Test the get_users_to_display function."""
    # Arrange
    mock_db_manager.get_users_to_display.return_value = {
        "success": True,
        "users": [{"username": "user1"}],
        "total_pages": 1
    }
    
    # Act
    result = api.get_users_to_display("currentuser", "user", 1, 10)
    
    # Assert
    assert result == {
        "success": True,
        "users": [{"username": "user1"}],
        "total_pages": 1
    }
    mock_db_manager.get_users_to_display.assert_called_once_with("currentuser", "user", 1, 10)