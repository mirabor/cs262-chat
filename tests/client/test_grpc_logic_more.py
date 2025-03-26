import pytest
import grpc
import time
from unittest.mock import patch, Mock, MagicMock, call, ANY

from src.client.grpc_logic import (
    ChatAppLogicGRPC, 
    with_retry_and_logging, 
    MAX_RETRIES, 
    RETRY_DELAY
)
from src.protocol.grpc import chat_pb2, chat_pb2_grpc, replication_pb2


# Mock a real RpcError - This approach directly subclasses Exception
class MockRpcError(Exception):
    """Mock for grpc.RpcError that works with isinstance checks."""
    
    def __init__(self, code=grpc.StatusCode.UNKNOWN, details=None):
        self._code = code
        self._details = details
        super().__init__(f"GRPC Error: {code}")
    
    def code(self):
        return self._code
    
    def details(self):
        return self._details if self._details else ""

    def __str__(self):
        return f"MockRpcError({self._code}, {self._details})"


# Make our mock pass isinstance checks
grpc.RpcError = MockRpcError
# This is a hack but should work for test purposes


def test_discover_replicas_success():
    """Test successful discovery of replicas in the network."""
    # Set up the mock environment
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub') as mock_stub_class, \
         patch('src.client.grpc_logic.logger') as mock_logger:
        
        # Create mock response with servers
        server1 = Mock()
        server1.server_id = "server1"
        server1.address = "localhost:50051"
        server1.role = "leader"
        
        server2 = Mock()
        server2.server_id = "server2"
        server2.address = "localhost:50052"
        server2.role = "follower"
        
        response = Mock()
        response.servers = [server1, server2]
        
        # Set up the replication stub
        mock_repl_stub = Mock()
        mock_repl_stub.GetNetworkState.return_value = response
        mock_stub_class.return_value = mock_repl_stub
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Manually call _discover_replicas to skip the initial call
        chat_logic._discover_replicas()
        
        # Verify results
        assert "localhost:50051" in chat_logic.known_replicas
        assert "localhost:50052" in chat_logic.known_replicas
        assert chat_logic.current_leader == "localhost:50051"
        assert mock_logger.info.call_count >= 2


def test_execute_with_failover_all_replicas_fail():
    """Test behavior when all replicas fail."""
    # Set up the mock environment
    with patch('grpc.insecure_channel') as mock_channel, \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub') as mock_stub_class, \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'), \
         patch('src.client.grpc_logic.logger'):
        
        # Create an instance
        chat_logic = ChatAppLogicGRPC()
        
        # Add a replica
        backup_address = "localhost:50052"
        chat_logic.known_replicas = {
            chat_logic.primary_address: True,
            backup_address: True
        }
        
        # Primary connection fails
        primary_error = MockRpcError(grpc.StatusCode.UNAVAILABLE)
        chat_logic.stub = Mock()
        primary_method = Mock(side_effect=primary_error)
        setattr(chat_logic.stub, "TestMethod", primary_method)
        
        # Backup connection also fails
        backup_stub = Mock()
        backup_error = MockRpcError(grpc.StatusCode.UNAVAILABLE)
        backup_method = Mock(side_effect=backup_error)
        setattr(backup_stub, "TestMethod", backup_method)
        
        # Make stub_class return our backup stub for the failover case
        mock_stub_class.return_value = backup_stub
        
        # Call the method - should raise exception
        with pytest.raises(Exception) as excinfo:
            chat_logic._execute_with_failover("TestMethod", Mock())
        
        # Verify the exception message
        assert "All known replicas are unavailable" in str(excinfo.value)
        
        # Verify replicas marked as unavailable
        assert chat_logic.known_replicas[chat_logic.primary_address] is False
        assert chat_logic.known_replicas[backup_address] is False


def test_handle_grpc_error():
    """Test handling of different gRPC errors."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Test UNAVAILABLE error
        error1 = MockRpcError(grpc.StatusCode.UNAVAILABLE, "Server unavailable")
        success1, msg1 = chat_logic._handle_grpc_error("test_op", error1)
        assert success1 is False
        assert "Service unavailable" in msg1
        
        # Test NOT_FOUND error
        error2 = MockRpcError(grpc.StatusCode.NOT_FOUND, "Resource not found")
        success2, msg2 = chat_logic._handle_grpc_error("test_op", error2)
        assert success2 is False
        assert "Resource not found" in msg2
        
        # Test PERMISSION_DENIED error
        error3 = MockRpcError(grpc.StatusCode.PERMISSION_DENIED, "No permission")
        success3, msg3 = chat_logic._handle_grpc_error("test_op", error3)
        assert success3 is False
        assert "Permission denied" in msg3
        
        # Test other error
        error4 = MockRpcError(grpc.StatusCode.INTERNAL, "Internal error")
        success4, msg4 = chat_logic._handle_grpc_error("test_op", error4)
        assert success4 is False
        assert "Failed to test_op" in msg4
        
        # Test error with no details
        error5 = MockRpcError(grpc.StatusCode.INVALID_ARGUMENT)
        error5.details = lambda: None  # Override to return None
        success5, msg5 = chat_logic._handle_grpc_error("test_op", error5)
        assert success5 is False
        assert "Failed to test_op" in msg5


def test_delete_messages():
    """Test the delete_messages method."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success = True
        mock_response.error_message = ""
        
        # Mock the method call
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response) as mock_exec:
            success, error = chat_logic.delete_messages("chat123", [1, 2, 3], "user1")
            
            # Verify result
            assert success is True
            assert error == ""
            
            # Verify correct arguments
            mock_exec.assert_called_once()
            method_name, request = mock_exec.call_args[0]
            assert method_name == "DeleteMessages"
            assert request.chat_id == "chat123"
            assert list(request.message_indices) == [1, 2, 3]
            assert request.current_user == "user1"


class TestClass:
    """Test class for the retry decorator."""
    
    def __init__(self):
        self.call_count = 0
    
    def _handle_grpc_error(self, method_name, error):
        return False, f"Error in {method_name}"
    
    @with_retry_and_logging("test_retry")
    def retry_success_eventually(self):
        """Succeed after a few attempts."""
        self.call_count += 1
        if self.call_count < 3:
            raise MockRpcError(grpc.StatusCode.UNAVAILABLE)
        return True, "Success"
    
    @with_retry_and_logging("test_max_retries")
    def retry_always_fail(self):
        """Always fail with RPC error."""
        self.call_count += 1
        raise MockRpcError(grpc.StatusCode.UNAVAILABLE)
    
    @with_retry_and_logging("test_non_rpc")
    def non_rpc_error(self):
        """Raise a non-RPC error."""
        self.call_count += 1
        raise ValueError("Regular error")


def test_retry_success_eventually():
    """Test retry mechanism eventually succeeding."""
    obj = TestClass()
    
    with patch('time.sleep') as mock_sleep, \
         patch('src.client.grpc_logic.logger'):
        result = obj.retry_success_eventually()
    
    assert obj.call_count == 3
    assert result == (True, "Success")
    assert mock_sleep.call_count == 2

def test_execute_with_failover_successful_failover():
    """Test successful failover to another replica."""
    with patch('grpc.insecure_channel') as mock_channel, \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub') as mock_stub_class, \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub') as mock_repl_stub_class, \
         patch.object(ChatAppLogicGRPC, '_discover_replicas') as mock_discover, \
         patch('src.client.grpc_logic.logger') as mock_logger:
        
        # Create an instance
        chat_logic = ChatAppLogicGRPC()
        
        # Set up replicas
        primary_address = chat_logic.primary_address
        backup_address = "localhost:50052"
        chat_logic.known_replicas = {
            primary_address: True,
            backup_address: True
        }
        
        # Primary connection fails
        primary_error = MockRpcError(grpc.StatusCode.UNAVAILABLE)
        chat_logic.stub = Mock()
        primary_method = Mock(side_effect=primary_error)
        setattr(chat_logic.stub, "TestMethod", primary_method)
        
        # Backup connection succeeds
        backup_stub = Mock()
        backup_response = Mock()
        backup_method = Mock(return_value=backup_response)
        setattr(backup_stub, "TestMethod", backup_method)
        
        # Set up channel and stubs
        mock_stub_class.return_value = backup_stub
        mock_repl_stub_class.return_value = Mock()
        
        # Call the method
        result = chat_logic._execute_with_failover("TestMethod", Mock())
        
        # Verify results
        assert result == backup_response
        assert chat_logic.primary_address == backup_address
        mock_logger.warning.assert_called_once()
        mock_logger.info.assert_called_with(f"Trying failover to replica at {backup_address}")
        
        # Verify channel was closed and recreated
        assert chat_logic.channel.close.call_count == 1
        assert mock_channel.call_count == 2  # initial + failover
        
        # Allow for multiple discover calls (initial + failover)
        assert mock_discover.call_count >= 1


def test_login_success():
    """Test successful login."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'), \
         patch('src.client.grpc_logic.hash_password', return_value="hashed_pass"), \
         patch('src.client.grpc_logic.logger'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success = True
        mock_response.error_message = ""
        
        # Mock the method call
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response):
            success, error = chat_logic.login("user1", "password123")
            
            # Verify result
            assert success is True
            assert error == ""


def test_get_users_to_display_success():
    """Test successful retrieval of users to display."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Mock the response
        mock_response = Mock()
        mock_response.usernames = ["user2", "user3"]
        mock_response.error_message = ""
        
        # Mock the method call
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response) as mock_exec:
            users, error = chat_logic.get_users_to_display("user1", "user", 1, 10)
            
            # Verify result
            assert users == ["user2", "user3"]
            assert error == ""
            
            # Verify correct arguments
            mock_exec.assert_called_once_with("GetUsersToDisplay", ANY)
            request = mock_exec.call_args[0][1]
            assert request.exclude_username == "user1"
            assert request.search_pattern == "user"
            assert request.current_page == 1
            assert request.users_per_page == 10


def test_login_failure():
    """Test failed login."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'), \
         patch('src.client.grpc_logic.hash_password', return_value="hashed_pass"), \
         patch('src.client.grpc_logic.logger'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Mock the response
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "Invalid credentials"
        
        # Mock the method call
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response):
            success, error = chat_logic.login("user1", "wrongpass")
            
            # Verify result
            assert success is False
            assert error == "Invalid credentials"


def test_get_chats_with_error():
    """Test get_chats with error response."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'), \
         patch('src.client.grpc_logic.logger'):
        
        chat_logic = ChatAppLogicGRPC()
        
        # Mock error response
        mock_response = Mock()
        mock_response.chats = []
        mock_response.error_message = "Error occurred"
        
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response):
            chats, error = chat_logic.get_chats("user1")
            assert chats == []
            assert error == "Error occurred"

def test_discover_replicas_failure():
    """Test failure case for replica discovery."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub') as mock_repl_stub, \
         patch('src.client.grpc_logic.logger') as mock_logger:
        
        # Create mock RPC error
        mock_error = MockRpcError(grpc.StatusCode.UNAVAILABLE, "Service unavailable")
        mock_repl_stub.return_value.GetNetworkState.side_effect = mock_error
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Verify the error was logged
        mock_logger.warning.assert_called_once_with(
            f"Failed to discover replicas: {mock_error}"
        )
        
        # Verify replicas list only contains the initial server
        assert list(chat_logic.known_replicas.keys()) == [chat_logic.primary_address]


def test_start_chat_failure():
    """Test failure case for starting a chat."""
    with patch('grpc.insecure_channel'), \
         patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub'), \
         patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub'), \
         patch.object(ChatAppLogicGRPC, '_discover_replicas'):
        
        # Create the instance
        chat_logic = ChatAppLogicGRPC()
        
        # Mock the response with failure
        mock_response = Mock()
        mock_response.success = False
        mock_response.error_message = "User not found"
        
        # Mock the method call
        with patch.object(chat_logic, '_execute_with_failover', return_value=mock_response):
            chat_id, error = chat_logic.start_chat("user1", "user2")
            
            # Verify result
            assert chat_id is None
            assert error == "User not found"