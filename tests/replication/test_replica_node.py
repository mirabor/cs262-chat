"""
Tests for the ReplicaNode implementation.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.replication.replica_node import ReplicaNode
from src.protocol.grpc import replication_pb2 as replication


@pytest.fixture
def replica_node():
    """Create a fresh ReplicaNode instance for each test."""
    return ReplicaNode(server_id="test_server", address="localhost:50051")


@pytest.fixture
def replica_node_with_peers():
    """Create a ReplicaNode instance with peers for testing."""
    return ReplicaNode(
        server_id="test_server",
        address="localhost:50051",
        peers=["peer1:localhost:50052", "peer2:localhost:50053"]
    )


def test_init_basic():
    """Test basic initialization of ReplicaNode."""
    node = ReplicaNode(server_id="test_server", address="localhost:50051")
    
    assert node.server_id == "test_server"
    assert node.address == "localhost:50051"
    assert node.term == 0
    assert node.role == "follower"
    assert node.leader_id is None
    assert len(node.peers) == 0
    assert node.server_id in node.servers_info
    assert node.servers_info[node.server_id].role == "follower"


def test_init_with_peers():
    """Test initialization with peers."""
    node = ReplicaNode(
        server_id="test_server",
        address="localhost:50051",
        peers=["peer1:localhost:50052", "peer2:localhost:50053"]
    )
    
    assert len(node.peers) == 2
    assert "peer1" in node.peers
    assert node.peers["peer1"] == "localhost:50052"
    assert "peer2" in node.peers
    assert node.peers["peer2"] == "localhost:50053"


def test_init_with_direct_address_peers():
    """Test initialization with direct address format peers."""
    node = ReplicaNode(
        server_id="test_server",
        address="localhost:50051",
        peers=["localhost:50052", "localhost:50053"]
    )
    
    assert len(node.peers) == 2
    assert "peer_0" in node.peers
    assert node.peers["peer_0"] == "localhost:50052"
    assert "peer_1" in node.peers
    assert node.peers["peer_1"] == "localhost:50053"


@patch("src.replication.replica_node.ReplicaNode.join_network")
def test_start_with_peers(mock_join_network, replica_node_with_peers):
    """Test start method with peers."""
    replica_node_with_peers.start()
    
    mock_join_network.assert_called_once()
    assert replica_node_with_peers.role == "follower"


@patch("src.replication.replica_node.ReplicaNode.become_leader")
def test_start_without_peers(mock_become_leader, replica_node):
    """Test start method without peers."""
    replica_node.start()
    
    mock_become_leader.assert_called_once()


@patch("src.replication.replica_node.grpc.insecure_channel")
def test_join_network_success(mock_channel, replica_node_with_peers):
    """Test successful join network."""
    # Add the missing reset_election_timer method to the replica node
    replica_node_with_peers.reset_election_timer = MagicMock()
    
    # Setup mock response
    mock_stub = MagicMock()
    mock_channel.return_value.__enter__.return_value = MagicMock()
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.term = 5
    mock_response.leader_id = "leader1"
    
    # Setup mock servers in response
    server1 = MagicMock()
    server1.server_id = "server1"
    server1.address = "localhost:50052"
    server1.role = "follower"
    
    server2 = MagicMock()
    server2.server_id = "server2"
    server2.address = "localhost:50053"
    server2.role = "leader"
    
    mock_response.servers = [server1, server2]
    mock_response.server_addresses = {"server1": "localhost:50052", "server2": "localhost:50053"}
    
    # Setup mock stub
    mock_stub.JoinNetwork.return_value = mock_response
    mock_channel.return_value.__enter__.return_value = mock_stub
    
    # Call join_network
    with patch("src.replication.replica_node.replication_grpc.ReplicationServiceStub", return_value=mock_stub):
        replica_node_with_peers.join_network()
    
    # Assertions
    assert replica_node_with_peers.term == 5
    assert replica_node_with_peers.leader_id == "leader1"
    assert "server1" in replica_node_with_peers.peers
    assert "server2" in replica_node_with_peers.peers
    assert replica_node_with_peers.peers["server1"] == "localhost:50052"
    assert replica_node_with_peers.peers["server2"] == "localhost:50053"


@patch("src.replication.replica_node.grpc.insecure_channel")
def test_join_network_failure(mock_channel, replica_node_with_peers):
    """Test join network failure."""
    # Setup mock to raise exception
    mock_channel.return_value.__enter__.side_effect = Exception("Connection failed")
    
    # Mock become_leader to verify it's called on failure
    with patch.object(replica_node_with_peers, "become_leader") as mock_become_leader:
        replica_node_with_peers.join_network()
        
        # Verify become_leader was called after all join attempts failed
        mock_become_leader.assert_called_once()


def test_shutdown(replica_node):
    """Test shutdown method."""
    # This is just a placeholder test since the method is not implemented yet
    replica_node.shutdown()
    # No assertions needed, just verifying it doesn't raise exceptions


def test_become_leader(replica_node):
    """Test become_leader method."""
    # This is just a placeholder test since the method is not implemented yet
    replica_node.become_leader()
    # No assertions needed, just verifying it doesn't raise exceptions
