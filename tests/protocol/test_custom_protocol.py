import pytest
from src.protocol.custom_protocol import CustomProtocol
from tests.protocol.base_protocol_test import BaseProtocolTest


class TestCustomProtocol(BaseProtocolTest):
    """Test Custom protocol implementation."""

    @pytest.fixture
    def protocol(self):
        return CustomProtocol()

    @pytest.mark.skip(reason="CustomProtocol is not implemented yet")
    def test_serialization(self, protocol, valid_message):
        super().test_serialization(protocol, valid_message)

    @pytest.mark.skip(reason="CustomProtocol is not implemented yet")
    def test_deserialization(self, protocol, valid_message):
        super().test_deserialization(protocol, valid_message)
