import pytest


class BaseProtocolTest:
    """Base test class for protocol implementations."""

    @pytest.fixture
    def protocol(self):
        """Should be implemented by child classes to return the protocol instance."""
        raise NotImplementedError()

    @pytest.fixture(
        params=[
            # Basic message
            {"key": "value"},
            # Empty message
            {},
            # Message with special characters
            {"special": "!@#$%^&*()", "quotes": '"quoted"', "escaped": "\\backslash"},
            # Message with different data types
            {
                "null": None,
                "bool": True,
                "int": 42,
                "float": 3.14159,
                "scientific": 1e-10,
            },
            # Deeply nested structure
            {"level1": {"level2": {"level3": {"level4": "deep value"}}}},
            # Large message with arrays
            {
                "numbers": list(range(100)),
                "strings": ["str" + str(i) for i in range(50)],
            },
            # Unicode characters
            {"unicode": "Hello, 世界! 🌍 😊", "emoji": "🎉 🚀 🎮 🎨 🎭"},
            # Chat application specific messages
            {
                "type": "message",
                "id": "msg123",
                "timestamp": "2025-02-11T13:14:15Z",
                "sender": "user123",
                "recipient": "user456",
                "content": "Hello, how are you?",
                "metadata": {"client": "web", "version": "1.0.0", "encrypted": True},
            },
            # Edge case: empty strings and arrays
            {
                "empty_string": "",
                "empty_array": [],
                "empty_object": {},
                "array_with_empty": ["", {}, []],
            },
            # Edge case: very long strings
            {"long_string": "x" * 1000000},
        ]
    )
    def valid_message(self, request):
        """Returns various test messages to verify protocol implementation.

        Each message tests different aspects of serialization/deserialization:

        - Basic messages

        - Empty messages

        - Special characters

        - Different data types

        - Nested structures

        - Large messages

        - Unicode support

        - Chat-specific messages

        - Edge cases

        """

        return request.param

    # @pytest.fixture
    # def valid_serialized(self):
    #     """Should be implemented by child classes to return valid serialized data."""
    #     raise NotImplementedError()

    def test_serialization(self, protocol, valid_message):
        """Test protocol serialization."""
        serialized = protocol.serialize(valid_message)
        assert isinstance(serialized, bytes)

        # Test round trip
        deserialized = protocol.deserialize(serialized)
        assert deserialized == valid_message

    def test_deserialization(self, protocol, valid_message):
        """Test protocol deserialization."""
        serialized = protocol.serialize(valid_message)
        assert isinstance(serialized, bytes)

        # Test round trip
        deserialized = protocol.deserialize(serialized)
        assert isinstance(deserialized, dict)
        assert deserialized == valid_message

    @pytest.mark.parametrize(
        "invalid_data",
        [
            b"invalid data",  # Random bytes
            b"",  # Empty bytes
            b"{",  # Incomplete JSON
            b"[1, 2, 3]",  # Array instead of object
            b"true",  # Boolean instead of object
            b"42",  # Number instead of object
            b"\xFF\xFF\xFF\xFF",  # Invalid UTF-8
            b"null",  # null instead of object
            b"\x00\x01\x02\x03",  # Binary data
            b"\n\t\r ",  # Only whitespace
        ],
    )
    def test_invalid_deserialization(self, protocol, invalid_data):
        """Test protocol deserialization with various types of invalid data.

        Tests handling of:
        - Random invalid bytes
        - Empty input
        - Malformed JSON
        - Wrong JSON types
        - Invalid UTF-8
        - Invalid JSON syntax
        - Binary data
        - JavaScript-specific values
        """
        with pytest.raises((ValueError, NotImplementedError)):
            protocol.deserialize(invalid_data)
