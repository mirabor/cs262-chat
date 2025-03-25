"""
Tests for the replication config module.
"""

import pytest
from src.replication.config import (
    HEARTBEAT_INTERVAL,
    ELECTION_TIMEOUT_MIN,
    ELECTION_TIMEOUT_MAX,
    MAX_MISSED_HEARTBEATS
)


def test_config_constants():
    """Test that config constants are defined with expected values."""
    assert HEARTBEAT_INTERVAL == 1
    assert ELECTION_TIMEOUT_MIN == 3
    assert ELECTION_TIMEOUT_MAX == 6
    assert MAX_MISSED_HEARTBEATS == 3
    
    # Test that the election timeout min is less than max
    assert ELECTION_TIMEOUT_MIN < ELECTION_TIMEOUT_MAX
    
    # Test that heartbeat interval is less than election timeout
    # (important for proper functioning of the consensus algorithm)
    assert HEARTBEAT_INTERVAL < ELECTION_TIMEOUT_MIN
