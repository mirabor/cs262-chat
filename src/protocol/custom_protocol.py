from .message_protocol import MessageProtocol


class CustomProtocol(MessageProtocol):
    """A custom binary protocol implementation."""

    def serialize(self, message: dict) -> bytes:
        # TODO:
        raise NotImplementedError("Custom serialization not implemented")

    def deserialize(self, data: bytes) -> dict:
        # TODO:
        raise NotImplementedError("Custom deserialization not implemented")
