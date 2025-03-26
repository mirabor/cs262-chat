"""
Tests for the ReplicationServicer implementation.
"""

import pytest
import grpc
from unittest.mock import MagicMock, patch
from src.services.replication_servicer import ReplicationServicer
from src.protocol.grpc import replication_pb2 as replication
from src.protocol.grpc import replication_pb2_grpc


@pytest.fixture
def mock_replica():
    """Create a mock replica for testing."""
    # Create a mock state object
    state = MagicMock()
    state.server_id = "test_server"
    state.address = "localhost:50051"
    state.role = "leader"  # Default to leader for most tests
    state.term = 1
    state.leader_id = "test_server"
    state.peers = {"peer1": "localhost:50052", "peer2": "localhost:50053"}
    
    # Create proper ServerInfo objects
    test_server_info = replication.ServerInfo()
    test_server_info.server_id = "test_server"
    test_server_info.address = "localhost:50051"
    test_server_info.role = "leader"
    
    peer1_info = replication.ServerInfo()
    peer1_info.server_id = "peer1"
    peer1_info.address = "localhost:50052"
    peer1_info.role = "follower"
    
    peer2_info = replication.ServerInfo()
    peer2_info.server_id = "peer2"
    peer2_info.address = "localhost:50053"
    peer2_info.role = "follower"
    
    state.servers_info = {
        "test_server": test_server_info,
        "peer1": peer1_info,
        "peer2": peer2_info
    }
    
    # Create the replica with the state
    replica = MagicMock()
    replica.state = state
    
    # Add election_manager for reset_election_timer calls
    replica.election_manager = MagicMock()
    return replica


@pytest.fixture
def servicer(mock_replica):
    """Create a ReplicationServicer instance with a mock replica."""
    return ReplicationServicer(mock_replica)


def test_heartbeat(servicer):
    """Test the Heartbeat method."""
    request = MagicMock()
    request.server_id = "peer1"
    request.term = 1
    request.role = "follower"
    context = MagicMock()
    
    # Call the method
    response = servicer.Heartbeat(request, context)
    
    # Verify the response
    assert response.success is True
    assert response.server_id == servicer.replica_state.server_id
    assert response.term == servicer.replica_state.term
    assert response.role == servicer.replica_state.role


def test_replicate_operation(servicer):
    """Test the ReplicateOperation method."""
    request = MagicMock()
    context = MagicMock()
    
    # Call the method
    servicer.ReplicateOperation(request, context)
    
    # Since it's not implemented yet, just verify it doesn't raise exceptions


def test_join_network_as_leader(servicer, mock_replica):
    """Test JoinNetwork when the servicer is the leader."""
    # Setup
    request = replication.JoinRequest()
    request.server_id = "new_server"
    request.address = "localhost:50054"
    context = MagicMock()
    
    # Call the method
    response = servicer.JoinNetwork(request, context)
    
    # Verify
    assert response.success is True
    assert response.leader_id == mock_replica.state.server_id
    assert response.term == mock_replica.state.term
    assert "new_server" in mock_replica.state.peers
    assert mock_replica.state.peers["new_server"] == "localhost:50054"
    assert "new_server" in mock_replica.state.servers_info


def test_join_network_as_follower_with_known_leader(servicer, mock_replica):
    """Test JoinNetwork when the servicer is a follower with a known leader."""
    mock_replica.state.role = "follower"
    mock_replica.state.leader_id = "leader1"
    mock_replica.state.peers["leader1"] = "localhost:50060"
    request = replication.JoinRequest()
    request.server_id = "new_server"
    request.address = "localhost:50054"
    context = MagicMock()

    # Create a mock JoinResponse
    mock_response = replication.JoinResponse()
    mock_response.success = True

    # Patch both the channel and the stub
    with patch("grpc.insecure_channel") as mock_channel, \
         patch("src.protocol.grpc.replication_pb2_grpc.ReplicationServiceStub") as mock_stub_class:

        mock_stub_instance = MagicMock()
        mock_stub_instance.JoinNetwork.return_value = mock_response
        mock_stub_class.return_value = mock_stub_instance

        mock_channel.return_value.__enter__.return_value = MagicMock()

        response = servicer.JoinNetwork(request, context)

    assert response.success is True
    mock_stub_instance.JoinNetwork.assert_called_once_with(request)


def test_join_network_as_follower_with_error(servicer, mock_replica):
    """Test JoinNetwork when the servicer is a follower and forwarding fails."""
    # Setup
    mock_replica.state.role = "follower"
    mock_replica.state.leader_id = "leader1"
    request = replication.JoinRequest()
    request.server_id = "new_server"
    request.address = "localhost:50054"
    context = MagicMock()
    
    # Mock the forwarding to leader to raise an exception
    with patch("grpc.insecure_channel") as mock_channel:
        mock_channel.return_value.__enter__.side_effect = Exception("Connection failed")
        
        # Call the method
        response = servicer.JoinNetwork(request, context)
    
    # Verify
    assert response.success is False
    context.set_code.assert_called_once_with(grpc.StatusCode.UNAVAILABLE)


def test_join_network_as_follower_without_leader(servicer, mock_replica):
    """Test JoinNetwork when the servicer is a follower without a known leader."""
    # Setup
    mock_replica.state.role = "follower"
    mock_replica.state.leader_id = None
    request = replication.JoinRequest()
    request.server_id = "new_server"
    request.address = "localhost:50054"
    context = MagicMock()
    
    # Call the method
    response = servicer.JoinNetwork(request, context)
    
    # Verify
    assert response.success is False
    context.set_code.assert_called_once_with(grpc.StatusCode.UNAVAILABLE)


def test_join_network_with_existing_server_id(servicer, mock_replica):
    """Test JoinNetwork when the server ID already exists with a different address."""
    # Setup
    mock_replica.state.peers["existing_server"] = "localhost:50055"
    request = replication.JoinRequest()
    request.server_id = "existing_server"
    request.address = "localhost:50056"
    context = MagicMock()
    
    # Call the method
    response = servicer.JoinNetwork(request, context)
    
    # Verify
    assert response.success is True
    assert mock_replica.state.peers["existing_server"] == "localhost:50056"  # Address should be updated


def test_join_network_with_existing_address(servicer, mock_replica):
    """Test JoinNetwork when the address already exists with a different server ID."""
    # Setup - Create a reverse mapping for testing
    address_to_id = {addr: id for id, addr in mock_replica.state.peers.items()}
    address_to_id["localhost:50057"] = "old_server"
    mock_replica.state.peers["old_server"] = "localhost:50057"
    
    # Create a ServerInfo for old_server
    old_server_info = replication.ServerInfo()
    old_server_info.server_id = "old_server"
    old_server_info.address = "localhost:50057"
    old_server_info.role = "follower"
    mock_replica.state.servers_info["old_server"] = old_server_info
    
    request = replication.JoinRequest()
    request.server_id = "new_server"
    request.address = "localhost:50057"
    context = MagicMock()
    
    # Call the method
    response = servicer.JoinNetwork(request, context)
    
    # Verify
    assert response.success is True
    assert "old_server" not in mock_replica.state.peers  # Old server should be removed
    assert mock_replica.state.peers["new_server"] == "localhost:50057"  # New server should be added


def test_get_network_state(servicer, mock_replica):
    """Test GetNetworkState method."""
    # Setup
    request = replication.NetworkStateRequest()
    request.server_id = "requester"
    context = MagicMock()
    
    # Call the method
    response = servicer.GetNetworkState(request, context)
    
    # Verify
    assert len(response.servers) == len(mock_replica.state.servers_info)
    assert response.leader_id == (mock_replica.state.leader_id if mock_replica.state.leader_id else "")
    assert response.term == mock_replica.state.term
    # 
    # # Call the method
    # with patch.object(replication, 'NetworkStateResponse', return_value=mock_response):
    #     response = servicer.GetNetworkState(request, context)
    # 
    # # Verify
    # assert response.leader_id == mock_replica.leader_id if mock_replica.leader_id else ""
    # assert response.term == mock_replica.term
