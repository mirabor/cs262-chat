import pytest
from src.protocol.custom_protocol import CustomProtocol
from tests.protocol.base_protocol_test import BaseProtocolTest


class TestCustomProtocol(BaseProtocolTest):
    """Test Custom protocol implementation."""

    @pytest.fixture
    def protocol(self):
        return CustomProtocol()
