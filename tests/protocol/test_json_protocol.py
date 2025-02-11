import pytest
from src.protocol.protocol_factory import JsonProtocol
from tests.protocol.base_protocol_test import BaseProtocolTest


class TestJsonProtocol(BaseProtocolTest):
    """Test JSON protocol implementation."""

    @pytest.fixture
    def protocol(self):
        return JsonProtocol()
