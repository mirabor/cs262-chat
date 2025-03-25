import unittest
from unittest.mock import Mock, patch, call
import pytest
import grpc
import time
import random

from src.client.grpc_logic import ChatAppLogicGRPC
from src.protocol.grpc import chat_pb2


class TestRetryMechanism(unittest.TestCase):
    def setUp(self):
        # Patch time.sleep to avoid actual delays during tests
        self.mock_sleep = patch('time.sleep').start()
        
        # Patch random.uniform and random.choice for deterministic testing
        self.mock_random_uniform = patch('random.uniform', return_value=0.05).start()
        self.mock_random_choice = patch('random.choice', side_effect=lambda x: x[0]).start()
        
        # Create mock channel and stub
        self.mock_channel = Mock()
        self.mock_stub = Mock()
        
        # Setup mock responses
        self.success_response = Mock()
        self.success_response.success = True
        self.success_response.error_message = ""
        
        # Setup the client with mocks
        self.mock_channel_creator = Mock(return_value=self.mock_channel)
        patch('grpc.insecure_channel', self.mock_channel_creator).start()
        
        self.mock_stub_class = Mock(return_value=self.mock_stub)
        patch('src.protocol.grpc.chat_pb2_grpc.ChatServiceStub', self.mock_stub_class).start()
        
        self.client = ChatAppLogicGRPC(host="localhost", port=50051)
        self.client.stub = self.mock_stub

    def tearDown(self):
        patch.stopall()  # Stop all patches
    
    def test_successful_request_no_retry(self):
        """Test that a successful request doesn't trigger retries."""
        # Setup mock response
        self.mock_stub.Login.return_value = self.success_response
        
        # Call the method
        success, _ = self.client.login("testuser", "password")
        
        # Verify the stub was called exactly once
        self.assertEqual(self.mock_stub.Login.call_count, 1)
        
        # Verify no sleep was called (no retries)
        self.mock_sleep.assert_not_called()
        
        # Verify success
        self.assertTrue(success)
    
    def test_retry_on_rpc_error(self):
        """Test that RPC errors trigger retries."""
        # Setup mock to raise error on first call, then succeed
        rpc_error = grpc.RpcError()
        rpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        rpc_error.details = lambda: "Server unavailable"
        
        self.mock_stub.Login.side_effect = [
            rpc_error,  # First call fails
            self.success_response  # Second call succeeds
        ]
        
        # Call the method
        success, _ = self.client.login("testuser", "password")
        
        # Verify the stub was called twice
        self.assertEqual(self.mock_stub.Login.call_count, 2)
        
        # Verify sleep was called once (for the retry)
        self.mock_sleep.assert_called_once()
        
        # Verify success
        self.assertTrue(success)
    
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        # Setup mock to always raise error
        rpc_error = grpc.RpcError()
        rpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        rpc_error.details = lambda: "Server unavailable"
        
        self.mock_stub.Login.side_effect = rpc_error
        
        # Call the method
        success, error_msg = self.client.login("testuser", "password")
        
        # Verify the stub was called max_retries + 1 times
        self.assertEqual(self.mock_stub.Login.call_count, self.client.max_retries + 1)
        
        # Verify sleep was called max_retries times
        self.assertEqual(self.mock_sleep.call_count, self.client.max_retries)
        
        # Verify failure
        self.assertFalse(success)
        self.assertIn("Failed to login", error_msg)
    
    def test_error_handling(self):
        """Test that the client properly handles errors."""
        # Setup mock to raise error then succeed
        rpc_error = grpc.RpcError()
        rpc_error.code = lambda: grpc.StatusCode.FAILED_PRECONDITION
        rpc_error.details = lambda: "Some error occurred"
        
        self.mock_stub.Login.side_effect = [
            rpc_error,  # First call fails
            self.success_response  # Second call succeeds
        ]
        
        # Call the method
        success, _ = self.client.login("testuser", "password")
        
        # Verify channels were created
        self.mock_channel_creator.assert_has_calls([
            call("localhost:50051"),  # Initial connection
            call("localhost:50051")    # Retry with same address (first in known_replicas)
        ])
        
        # Verify success
        self.assertTrue(success)
    
    def test_replica_switching(self):
        """Test that the client switches to different replicas on failures."""
        # Add known replicas
        self.client.known_replicas = ["localhost:50051", "127.0.0.1:5555", "127.0.0.1:5556"]
        
        # Setup mock to raise errors for first two replicas
        rpc_error1 = grpc.RpcError()
        rpc_error1.code = lambda: grpc.StatusCode.UNAVAILABLE
        rpc_error1.details = lambda: "Server unavailable"
        
        rpc_error2 = grpc.RpcError()
        rpc_error2.code = lambda: grpc.StatusCode.UNAVAILABLE
        rpc_error2.details = lambda: "Server unavailable"
        
        self.mock_stub.Login.side_effect = [
            rpc_error1,  # First replica fails
            rpc_error2,  # Second replica fails
            self.success_response  # Third replica succeeds
        ]
        
        # Call the method
        success, _ = self.client.login("testuser", "password")
        
        # Verify channels were created for different replicas
        self.mock_channel_creator.assert_has_calls([
            call("localhost:50051"),  # Initial connection
            call("127.0.0.1:5555"),   # First retry
            call("127.0.0.1:5556")    # Second retry
        ])
        
        # Verify success
        self.assertTrue(success)
    
    def test_exponential_backoff(self):
        """Test that exponential backoff is used for retries."""
        # Setup mock to always raise error
        rpc_error = grpc.RpcError()
        rpc_error.code = lambda: grpc.StatusCode.UNAVAILABLE
        rpc_error.details = lambda: "Server unavailable"
        
        self.mock_stub.Login.side_effect = rpc_error
        
        # Call the method
        self.client.login("testuser", "password")
        
        # Verify sleep was called with increasing delays
        expected_delays = []
        delay = self.client.retry_delay
        for _ in range(self.client.max_retries):
            expected_delays.append(min(delay, 5) + 0.05)
            delay *= 2
        
        actual_calls = [call[0][0] for call in self.mock_sleep.call_args_list]
        self.assertEqual(actual_calls, expected_delays)
    
    def test_metadata_extraction(self):
        """Test that replica information is extracted from response metadata."""
        # Create mock metadata
        mock_metadata = [
            ('replicas', 'localhost:50051,127.0.0.1:5555,127.0.0.1:5556')
        ]
        
        # Extract metadata
        replicas = self.client._extract_metadata(mock_metadata)
        
        # Verify extraction
        self.assertEqual(replicas, ['localhost:50051', '127.0.0.1:5555', '127.0.0.1:5556'])
    
    def test_update_replicas(self):
        """Test that replica information is updated correctly."""
        # Create mock metadata
        mock_metadata = [
            ('replicas', 'localhost:50051,127.0.0.1:5555,127.0.0.1:5556')
        ]
        
        # Set initial known replicas
        self.client.known_replicas = ['localhost:50051']
        
        # Update replicas
        self.client._update_replicas(mock_metadata)
        
        # Verify known replicas were updated (order doesn't matter since we use set)
        expected_replicas = ['localhost:50051', '127.0.0.1:5555', '127.0.0.1:5556']
        self.assertEqual(sorted(self.client.known_replicas), sorted(expected_replicas))


if __name__ == '__main__':
    unittest.main()
