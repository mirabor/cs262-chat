import unittest
from unittest.mock import Mock, patch, MagicMock, call
import time
import grpc

from src.replication.heartbeat_manager import HeartbeatManager
from src.replication.replica_state import ReplicaState
import src.protocol.grpc.replication_pb2 as replication
import src.protocol.grpc.replication_pb2_grpc as replication_grpc
from src.replication.config import HEARTBEAT_INTERVAL, MAX_MISSED_HEARTBEATS


class TestHeartbeatManager(unittest.TestCase):
    def setUp(self):
        # Create a mock state
        self.state = Mock(spec=ReplicaState)
        self.state.server_id = "server1"
        self.state.address = "localhost:50051"
        self.state.term = 1
        self.state.role = "follower"
        self.state.leader_id = None
        self.state.peers = {}
        self.state.servers_info = {}
        self.state.is_running = True
        
        # Create the heartbeat manager
        self.heartbeat_manager = HeartbeatManager(self.state)
        
        # Create a mock election manager
        self.election_manager = Mock()
        self.heartbeat_manager.set_election_manager(self.election_manager)

    @patch('time.sleep')  # Patch sleep to avoid actual waiting
    @patch('src.replication.heartbeat_manager.logger')
    def test_heartbeat_loop_as_leader(self, mock_logger, mock_sleep):
        """Test the heartbeat loop when the node is a leader."""
        # Set up the state as leader
        self.state.role = "leader"
        
        # Mock _send_heartbeats_as_leader to track calls
        self.heartbeat_manager._send_heartbeats_as_leader = Mock()
        
        # Set up a side effect to stop the loop after one iteration
        def stop_loop(*args, **kwargs):
            self.state.is_running = False
            
        mock_sleep.side_effect = stop_loop
        
        # Run the heartbeat loop
        self.heartbeat_manager.heartbeat_loop()
        
        # Verify _send_heartbeats_as_leader was called
        self.heartbeat_manager._send_heartbeats_as_leader.assert_called_once()
        
        # Verify sleep was called with the correct interval
        mock_sleep.assert_called_once_with(HEARTBEAT_INTERVAL)

    @patch('time.sleep')
    @patch('src.replication.heartbeat_manager.logger')
    def test_heartbeat_loop_as_follower(self, mock_logger, mock_sleep):
        """Test the heartbeat loop when the node is a follower with a leader."""
        # Set up the state as follower with a leader
        self.state.role = "follower"
        self.state.leader_id = "server2"
        
        # Mock _check_leader_liveness to track calls
        self.heartbeat_manager._check_leader_liveness = Mock()
        
        # Set up a side effect to stop the loop after one iteration
        def stop_loop(*args, **kwargs):
            self.state.is_running = False
            
        mock_sleep.side_effect = stop_loop
        
        # Run the heartbeat loop
        self.heartbeat_manager.heartbeat_loop()
        
        # Verify _check_leader_liveness was called
        self.heartbeat_manager._check_leader_liveness.assert_called_once()
        
        # Verify sleep was called with the correct interval
        mock_sleep.assert_called_once_with(HEARTBEAT_INTERVAL)

    @patch('time.sleep')
    @patch('src.replication.heartbeat_manager.logger')
    def test_heartbeat_loop_exception(self, mock_logger, mock_sleep):
        """Test the heartbeat loop when an exception occurs."""
        # Set up the state as leader
        self.state.role = "leader"
        
        # Mock _send_heartbeats_as_leader to raise an exception
        self.heartbeat_manager._send_heartbeats_as_leader = Mock(side_effect=Exception("Test exception"))
        
        # Set up a side effect to stop the loop after one iteration
        call_count = 0
        def stop_loop(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:  # Allow for both HEARTBEAT_INTERVAL and error sleep
                self.state.is_running = False
            
        mock_sleep.side_effect = stop_loop
        
        # Run the heartbeat loop
        self.heartbeat_manager.heartbeat_loop()
        
        # Verify the exception was logged - using assert_called instead of assert_called_once
        # because the error might be logged multiple times depending on the loop execution
        self.assertTrue(mock_logger.error.called)
        mock_logger.error.assert_called_with("Error in heartbeat loop: Test exception")
        
        # Verify sleep was called with 1 second after the exception
        mock_sleep.assert_any_call(1)

    @patch('grpc.insecure_channel')
    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_send_heartbeats_as_leader_success(self, mock_logger, mock_time, mock_channel):
        """Test sending heartbeats as leader with successful responses."""
        # Set up the state as leader with peers
        self.state.role = "leader"
        self.state.peers = {"server2": "localhost:50052", "server3": "localhost:50053"}
        
        # Mock time.time() to return a consistent value
        mock_time.return_value = 1000
        
        # Set up the mock channel and stub
        mock_stub = Mock()
        mock_channel.return_value.__enter__.return_value = Mock()
        mock_channel_context = mock_channel.return_value.__enter__.return_value
        mock_stub_instance = mock_stub.return_value
        
        # Create a mock for the ReplicationServiceStub
        with patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub', return_value=mock_stub_instance):
            # Set up the mock response
            mock_response = Mock()
            mock_response.term = 1  # Same term as the leader
            mock_response.role = "follower"
            mock_stub_instance.Heartbeat.return_value = mock_response
            
            # Call the method
            last_heartbeat_time = {}
            connection_failure_count = {}
            self.heartbeat_manager._send_heartbeats_as_leader(last_heartbeat_time, connection_failure_count)
            
            # Verify the stub was created for each peer
            self.assertEqual(mock_channel.call_count, 2)
            
            # Verify Heartbeat was called for each peer
            self.assertEqual(mock_stub_instance.Heartbeat.call_count, 2)
            
            # Verify the last heartbeat time was updated for each peer
            self.assertEqual(len(last_heartbeat_time), 2)
            self.assertEqual(last_heartbeat_time["server2"], 1000)
            self.assertEqual(last_heartbeat_time["server3"], 1000)
            
            # Verify the connection failure count was reset for each peer
            self.assertEqual(connection_failure_count["server2"], 0)
            self.assertEqual(connection_failure_count["server3"], 0)
            
            # Verify server info was updated
            self.assertEqual(len(self.state.servers_info), 2)

    @patch('grpc.insecure_channel')
    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_send_heartbeats_as_leader_higher_term(self, mock_logger, mock_time, mock_channel):
        """Test sending heartbeats as leader and discovering a higher term."""
        # Set up the state as leader with peers
        self.state.role = "leader"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Mock time.time() to return a consistent value
        mock_time.return_value = 1000
        
        # Set up the mock channel and stub
        mock_stub = Mock()
        mock_channel.return_value.__enter__.return_value = Mock()
        mock_channel_context = mock_channel.return_value.__enter__.return_value
        mock_stub_instance = mock_stub.return_value
        
        # Create a mock for the ReplicationServiceStub
        with patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub', return_value=mock_stub_instance):
            # Set up the mock response with higher term
            mock_response = Mock()
            mock_response.term = 2  # Higher term than the leader (1)
            mock_response.role = "leader"
            mock_stub_instance.Heartbeat.return_value = mock_response
            
            # Call the method
            last_heartbeat_time = {}
            connection_failure_count = {}
            self.heartbeat_manager._send_heartbeats_as_leader(last_heartbeat_time, connection_failure_count)
            
            # Verify the leader reverted to follower
            self.assertEqual(self.state.term, 2)
            self.assertEqual(self.state.role, "follower")
            self.assertIsNone(self.state.leader_id)
            
            # Verify the election timer was reset
            self.election_manager.reset_election_timer.assert_called_once()
            
            # Verify the info was logged
            mock_logger.info.assert_called_once_with("Discovered higher term 2, reverting to follower")

    @patch('grpc.insecure_channel')
    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_send_heartbeats_as_leader_connection_failure(self, mock_logger, mock_time, mock_channel):
        """Test sending heartbeats as leader with connection failures."""
        # Set up the state as leader with peers
        self.state.role = "leader"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Mock time.time() to return a consistent value
        mock_time.return_value = 1000
        
        # Set up the mock channel to raise an exception
        mock_channel.return_value.__enter__.side_effect = Exception("Connection failed")
        
        # Call the method
        last_heartbeat_time = {}
        connection_failure_count = {}
        self.heartbeat_manager._send_heartbeats_as_leader(last_heartbeat_time, connection_failure_count)
        
        # Verify the connection failure count was incremented
        self.assertEqual(connection_failure_count["server2"], 1)
        
        # Verify the warning was logged
        mock_logger.warning.assert_called_once_with(
            "Failed to send heartbeat to server2 at localhost:50052: Connection failed"
        )

    @patch('grpc.insecure_channel')
    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_send_heartbeats_as_leader_remove_unresponsive_peer(self, mock_logger, mock_time, mock_channel):
        """Test removing an unresponsive peer after too many failures."""
        # Set up the state as leader with peers
        self.state.role = "leader"
        self.state.peers = {"server2": "localhost:50052"}
        self.state.servers_info = {"server2": Mock()}
        
        # Mock time.time() to return a consistent value
        current_time = 1000
        mock_time.return_value = current_time
        
        # Set up the mock channel to raise an exception
        mock_channel.return_value.__enter__.side_effect = Exception("Connection failed")
        
        # Set up last heartbeat time to be older than the threshold
        last_heartbeat_time = {"server2": current_time - (MAX_MISSED_HEARTBEATS * HEARTBEAT_INTERVAL + 1)}
        connection_failure_count = {"server2": MAX_MISSED_HEARTBEATS}
        
        # Call the method
        self.heartbeat_manager._send_heartbeats_as_leader(last_heartbeat_time, connection_failure_count)
        
        # Verify the peer was removed
        self.assertEqual(len(self.state.peers), 0)
        self.assertEqual(len(self.state.servers_info), 0)
        self.assertEqual(len(last_heartbeat_time), 0)
        self.assertEqual(len(connection_failure_count), 0)
        
        # Verify the warning was logged
        mock_logger.warning.assert_any_call("Peer server2 has been unresponsive, removing from peers")

    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_check_leader_liveness_leader_timeout(self, mock_logger, mock_time):
        """Test checking leader liveness when the leader has timed out."""
        # Set up the state as follower with a leader
        self.state.role = "follower"
        self.state.leader_id = "server2"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Mock time.time() to return a value that indicates leader timeout
        current_time = 1000
        mock_time.return_value = current_time
        
        # Set up last heartbeat time to be older than the threshold
        last_heartbeat_time = {"server2": current_time - (MAX_MISSED_HEARTBEATS * HEARTBEAT_INTERVAL + 1)}
        connection_failure_count = {}
        
        # Call the method
        self.heartbeat_manager._check_leader_liveness(last_heartbeat_time, connection_failure_count)
        
        # Verify the leader was reset
        self.assertIsNone(self.state.leader_id)
        
        # Verify the election timer was reset
        self.election_manager.reset_election_timer.assert_called_once()
        
        # Verify the warning was logged
        mock_logger.warning.assert_called_once_with("Leader server2 has been unresponsive")

    @patch('time.time')
    @patch('src.replication.heartbeat_manager.logger')
    def test_check_leader_liveness_connection_failures(self, mock_logger, mock_time):
        """Test checking leader liveness when there are too many connection failures."""
        # Set up the state as follower with a leader
        self.state.role = "follower"
        self.state.leader_id = "server2"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Set up connection failure count to exceed the threshold
        last_heartbeat_time = {}
        connection_failure_count = {"server2": MAX_MISSED_HEARTBEATS}
        
        # Call the method
        self.heartbeat_manager._check_leader_liveness(last_heartbeat_time, connection_failure_count)
        
        # Verify the leader was reset
        self.assertIsNone(self.state.leader_id)
        
        # Verify the election timer was reset
        self.election_manager.reset_election_timer.assert_called_once()
        
        # Verify the warning was logged
        mock_logger.warning.assert_called_once_with("Leader server2 has been unreachable")

    @patch('grpc.insecure_channel')
    @patch('src.replication.heartbeat_manager.logger')
    def test_check_leader_status_success(self, mock_logger, mock_channel):
        """Test checking leader status with a successful response."""
        # Set up the state as follower with a leader
        self.state.role = "follower"
        self.state.leader_id = "server2"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Set up the mock channel and stub
        mock_stub = Mock()
        mock_channel.return_value.__enter__.return_value = Mock()
        mock_channel_context = mock_channel.return_value.__enter__.return_value
        mock_stub_instance = mock_stub.return_value
        
        # Create a mock for the ReplicationServiceStub
        with patch('src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub', return_value=mock_stub_instance):
            # Set up the mock response
            mock_response = Mock()
            mock_stub_instance.Heartbeat.return_value = mock_response
            
            # Call the method
            result = self.heartbeat_manager.check_leader_status()
            
            # Verify the result is True (leader is responsive)
            self.assertTrue(result)
            
            # Verify the debug message was logged
            mock_logger.debug.assert_called_once_with(
                "Checking status of leader server2 at localhost:50052"
            )

    @patch('grpc.insecure_channel')
    @patch('src.replication.heartbeat_manager.logger')
    def test_check_leader_status_failure(self, mock_logger, mock_channel):
        """Test checking leader status with a connection failure."""
        # Set up the state as follower with a leader
        self.state.role = "follower"
        self.state.leader_id = "server2"
        self.state.peers = {"server2": "localhost:50052"}
        
        # Set up the mock channel to raise an exception
        mock_channel.return_value.__enter__.side_effect = Exception("Connection failed")
        
        # Call the method
        result = self.heartbeat_manager.check_leader_status()
        
        # Verify the result is False (leader is not responsive)
        self.assertFalse(result)
        
        # Verify the warning was logged
        mock_logger.warning.assert_called_once_with(
            "Leader server2 appears to be down: Connection failed"
        )
        
        # Verify the election was started
        self.election_manager.start_election.assert_called_once()

    def test_check_leader_status_no_leader(self):
        """Test checking leader status when there is no leader."""
        # Set up the state as follower with no leader
        self.state.role = "follower"
        self.state.leader_id = None
        
        # Call the method
        result = self.heartbeat_manager.check_leader_status()
        
        # Verify the result is None (no leader to check)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
