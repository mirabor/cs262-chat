import pytest
from src.protocol.message_protocol import MessageProtocol
from src.protocol.protocol_factory import ProtocolFactory, JsonProtocol, CustomProtocol


class TestProtocolFactory:
    """Test the protocol factory functionality."""
    
    class TestProtocol(MessageProtocol):
        """A test protocol implementation."""
        def serialize(self, message: dict) -> bytes:
            return b"test"
        
        def deserialize(self, data: bytes) -> dict:
            return {"test": "data"}
    
    def test_register_protocol(self):
        """Test registering a new protocol."""
        ProtocolFactory.register_protocol("test", self.TestProtocol)
        protocol = ProtocolFactory.get_protocol("test")
        assert isinstance(protocol, self.TestProtocol)
    
    def test_register_invalid_protocol(self):
        """Test registering an invalid protocol class."""
        class InvalidProtocol:
            pass
        
        with pytest.raises(TypeError):
            ProtocolFactory.register_protocol("invalid", InvalidProtocol)
    
    def test_get_unknown_protocol(self):
        """Test getting an unknown protocol."""
        with pytest.raises(ValueError):
            ProtocolFactory.get_protocol("unknown")
    
    def test_get_json_protocol(self):
        """Test getting the JSON protocol."""
        protocol = ProtocolFactory.get_protocol("json")
        assert isinstance(protocol, JsonProtocol)
    
    def test_get_custom_protocol(self):
        """Test getting the custom protocol."""
        protocol = ProtocolFactory.get_protocol("custom")
        assert isinstance(protocol, CustomProtocol)
