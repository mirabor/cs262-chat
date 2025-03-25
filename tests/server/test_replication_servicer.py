"""
Tests for the ReplicationServicer implementation.
"""

import pytest
from src.services.replication_servicer import ReplicationServicer
from src.protocol.grpc import replication_pb2


@pytest.fixture
def servicer():
    """Create a fresh ReplicationServicer instance for each test."""
    return ReplicationServicer()


def test_append_entries_basic(servicer):
    """Test basic AppendEntries functionality."""
    request = replication_pb2.EntriesRequest(
        term=1,
        leader_id="leader1",
        prev_log_index=0,
        prev_log_term=0,
        entries=[],  # Empty entries for heartbeat
        leader_commit=0,
    )

    response = servicer.AppendEntries(request, None)
    assert response.success
    assert response.term == 1
    assert servicer.current_term == 1


def test_append_entries_with_entries(servicer):
    """Test AppendEntries with actual log entries."""
    entry = replication_pb2.LogEntry(term=1, index=1, command=b"test command")

    request = replication_pb2.EntriesRequest(
        term=1,
        leader_id="leader1",
        prev_log_index=0,
        prev_log_term=0,
        entries=[entry],
        leader_commit=0,
    )

    response = servicer.AppendEntries(request, None)
    assert response.success
    assert response.term == 1


def test_append_entries_old_term(servicer):
    """Test AppendEntries with outdated term."""
    # Set current term higher
    servicer.current_term = 2

    request = replication_pb2.EntriesRequest(
        term=1,  # Old term
        leader_id="leader1",
        prev_log_index=0,
        prev_log_term=0,
        entries=[],
        leader_commit=0,
    )

    response = servicer.AppendEntries(request, None)
    assert not response.success
    assert response.term == 2
    assert servicer.current_term == 2


def test_request_vote_basic(servicer):
    """Test basic RequestVote functionality."""
    request = replication_pb2.VoteRequest(
        term=1, candidate_id="candidate1", last_log_index=0, last_log_term=0
    )

    response = servicer.RequestVote(request, None)
    assert response.vote_granted
    assert response.term == 1
    assert servicer.voted_for == "candidate1"


def test_request_vote_already_voted(servicer):
    """Test RequestVote when already voted in current term."""
    # First vote
    servicer.current_term = 1
    servicer.voted_for = "candidate1"

    # Second vote attempt for different candidate
    request = replication_pb2.VoteRequest(
        term=1, candidate_id="candidate2", last_log_index=0, last_log_term=0
    )

    response = servicer.RequestVote(request, None)
    assert not response.vote_granted
    assert response.term == 1
    assert servicer.voted_for == "candidate1"


def test_request_vote_old_term(servicer):
    """Test RequestVote with outdated term."""
    servicer.current_term = 2

    request = replication_pb2.VoteRequest(
        term=1, candidate_id="candidate1", last_log_index=0, last_log_term=0
    )

    response = servicer.RequestVote(request, None)
    assert not response.vote_granted
    assert response.term == 2
