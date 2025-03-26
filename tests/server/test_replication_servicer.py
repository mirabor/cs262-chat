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
