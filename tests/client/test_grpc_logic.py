from unittest.mock import Mock, patch
import pytest
import grpc
from src.client.grpc_logic import ChatAppLogicGRPC
from src.protocol.grpc import chat_pb2
from src.client.utils import hash_password


@pytest.fixture
def mock_stub():
    # Create a mock stub with all the required methods
    stub = Mock()
    
    # Mock Signup
    mock_signup_response = Mock()
    mock_signup_response.success = True
    mock_signup_response.error_message = ""
    stub.Signup.return_value = mock_signup_response
    
    # Mock Login
    mock_login_response = Mock()
    mock_login_response.success = True
    mock_login_response.error_message = ""
    stub.Login.return_value = mock_login_response
    
    # Mock GetUsersToDisplay
    mock_users_response = Mock()
    mock_users_response.usernames = ["user1", "user2"]
    mock_users_response.error_message = ""
    stub.GetUsersToDisplay.return_value = mock_users_response
    
    # Mock SendChatMessage
    mock_send_response = Mock()
    mock_send_response.success = True
    mock_send_response.error_message = ""
    stub.SendChatMessage.return_value = mock_send_response
    
    # Mock GetMessages
    mock_message = Mock()
    mock_message.sender = "user1"
    mock_message.content = "Hello!"
    mock_message.timestamp = 1234567890
    mock_messages_response = Mock()
    mock_messages_response.messages = [mock_message]
    mock_messages_response.error_message = ""
    stub.GetMessages.return_value = mock_messages_response
    
    return stub


@pytest.fixture
def chat_logic(mock_stub):
    # Mock the gRPC channel and stub creation
    with patch('grpc.insecure_channel') as mock_channel_creator:
        # Create a mock channel that returns our mock stub
        mock_channel = Mock()
        mock_channel_creator.return_value = mock_channel
        
        # Mock the stub class to return our mock stub
        with patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub') as mock_stub_class:
            mock_stub_class.return_value = mock_stub
            chat_logic = ChatAppLogicGRPC()
            chat_logic.stub = mock_stub  # Ensure we're using our mock stub
            return chat_logic


def test_signup_success(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.Signup.return_value = mock_response

    # Test
    success, message = chat_logic.signup("testuser", "Test User", "password123")
    assert success
    assert message == ""

    # Verify correct request
    mock_stub.Signup.assert_called_once()
    request = mock_stub.Signup.call_args[0][0]
    assert request.username == "testuser"
    assert request.nickname == "Test User"
    assert request.password == hash_password("password123")


def test_signup_failure_empty_fields(chat_logic, mock_stub):
    success, message = chat_logic.signup("", "", "")
    assert not success
    assert message == "All fields are required."
    mock_stub.Signup.assert_not_called()


def test_login_success(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.Login.return_value = mock_response

    # Test
    success, message = chat_logic.login("testuser", "password123")
    assert success
    assert message == ""

    # Verify correct request
    mock_stub.Login.assert_called_once()
    request = mock_stub.Login.call_args[0][0]
    assert request.username == "testuser"
    assert request.password == hash_password("password123")


def test_login_failure_empty_fields(chat_logic, mock_stub):
    success, message = chat_logic.login("", "")
    assert not success
    assert message == "Username and password are required."
    mock_stub.Login.assert_not_called()


def test_get_users_to_display(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.usernames = ["user1", "user2"]
    mock_response.error_message = ""
    mock_stub.GetUsersToDisplay.return_value = mock_response

    # Test
    users, error = chat_logic.get_users_to_display("currentuser", "", 1, 10)
    
    # Verify results
    assert len(users) == 2
    assert users == ["user1", "user2"]
    assert error == ""

    # Verify correct request
    mock_stub.GetUsersToDisplay.assert_called_once()
    request = mock_stub.GetUsersToDisplay.call_args[0][0]
    assert request.exclude_username == "currentuser"
    assert request.search_pattern == ""
    assert request.current_page == 1
    assert request.users_per_page == 10


def test_send_chat_message(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.SendChatMessage.return_value = mock_response

    # Test
    success, message = chat_logic.send_chat_message("chat123", "sender", "Hello!")
    assert success
    assert message == ""

    # Verify correct request
    mock_stub.SendChatMessage.assert_called_once()
    request = mock_stub.SendChatMessage.call_args[0][0]
    assert request.chat_id == "chat123"
    assert request.sender == "sender"
    assert request.content == "Hello!"


def test_get_messages(chat_logic, mock_stub):
    # Create a mock message
    mock_message = Mock()
    mock_message.sender = "user1"
    mock_message.content = "Hello!"
    mock_message.timestamp = 1234567890

    # Set up the mock response
    mock_response = Mock()
    mock_response.messages = [mock_message]
    mock_response.error_message = ""
    mock_stub.GetMessages.return_value = mock_response

    # Test
    messages, error = chat_logic.get_messages("chat123", "user1")
    
    # Verify results
    assert len(messages) == 1
    assert messages[0]["sender"] == "user1"
    assert messages[0]["content"] == "Hello!"
    assert messages[0]["timestamp"] == 1234567890
    assert error == ""

    # Verify correct request
    mock_stub.GetMessages.assert_called_once()
    request = mock_stub.GetMessages.call_args[0][0]
    assert request.chat_id == "chat123"
    assert request.current_user == "user1"


def test_get_messages_error(chat_logic, mock_stub):
    # Set up error response
    mock_response = Mock()
    mock_response.messages = []
    mock_response.error_message = "Failed to get messages"
    mock_stub.GetMessages.return_value = mock_response

    # Test
    messages, error = chat_logic.get_messages("chat123", "user1")
    assert len(messages) == 0
    assert error == "Failed to get messages"


def test_get_chats(chat_logic, mock_stub):
    # Mock response
    mock_chat = Mock()
    mock_chat.chat_id = "chat123"
    mock_chat.other_user = "user2"
    mock_chat.unread_count = 0
    mock_response = Mock()
    mock_response.chats = [mock_chat]
    mock_response.error_message = ""
    mock_stub.GetChats.return_value = mock_response

    # Test
    chats, error = chat_logic.get_chats("user1")
    assert len(chats) == 1
    assert chats[0]["chat_id"] == "chat123"
    assert error == ""


def test_get_other_user_in_chat(chat_logic, mock_stub):
    # First call get_chats to populate the cache
    mock_chat = Mock()
    mock_chat.chat_id = "chat123"
    mock_chat.other_user = "user2"
    mock_chat.unread_count = 0
    mock_chats_response = Mock()
    mock_chats_response.chats = [mock_chat]
    mock_chats_response.error_message = ""
    mock_stub.GetChats.return_value = mock_chats_response
    chat_logic.get_chats("user1")

    # Test
    other_user = chat_logic.get_other_user_in_chat("chat123")
    assert other_user == "user2"


def test_start_chat(chat_logic, mock_stub):
    # Mock response
    mock_chat = Mock()
    mock_chat.chat_id = "chat123"
    mock_response = Mock()
    mock_response.chat = mock_chat
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.StartChat.return_value = mock_response

    # Test
    chat_id, error = chat_logic.start_chat("user1", "user2")
    assert chat_id == "chat123"
    assert error == ""


def test_get_user_message_limit(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.limit = 100
    mock_response.error_message = ""
    mock_stub.GetUserMessageLimit.return_value = mock_response

    # Test
    limit, error = chat_logic.get_user_message_limit("user1")
    assert limit == 100
    assert error == ""


def test_save_settings(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.SaveSettings.return_value = mock_response

    # Test
    success, error = chat_logic.save_settings("user1", "100")
    assert success
    assert error == ""
    
    # Verify the correct request was made
    mock_stub.SaveSettings.assert_called_once()


def test_delete_account(chat_logic, mock_stub):
    # Mock response
    mock_response = Mock()
    mock_response.success = True
    mock_response.error_message = ""
    mock_stub.DeleteUser.return_value = mock_response

    # Test
    success, error = chat_logic.delete_account("user1")
    assert success
    assert error == ""
