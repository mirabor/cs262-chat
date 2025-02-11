from typing import Type
from .message_protocol import MessageProtocol
from .custom_protocol import CustomProtocol
import json


class JsonProtocol(MessageProtocol):
    def serialize(self, message: dict) -> bytes:
        """Serialize a dictionary into JSON-encoded bytes."""
        return json.dumps(message).encode("utf-8")

    def deserialize(self, data: bytes) -> dict:
        """Deserialize JSON-encoded bytes back into a dictionary."""
        return json.loads(data.decode("utf-8"))c


class ProtocolFactory:
    """
    A factory class for creating protocol instances.
    """

    _protocols = {"json": JsonProtocol, "custom": CustomProtocol}

    @classmethod
    def register_protocol(cls, name: str, protocol_class: Type[MessageProtocol]):
        """
        Register a new protocol class with the factory.
        :param name: The protocol name (identifier).
        :param protocol_class: The protocol class (must be a subclass of MessageProtocol).
        """
        if not issubclass(protocol_class, MessageProtocol):
            raise TypeError(f"{protocol_class} is not a subclass of MessageProtocol")
        cls._protocols[name] = protocol_class

    @classmethod
    def get_protocol(cls, protocol_name: str) -> MessageProtocol:
        """
        Retrieve an instance of the specified protocol.
        :param protocol_name: The name of the protocol ('json' or 'custom').
        :return: An instance of the requested MessageProtocol.
        """
        protocol_class = cls._protocols.get(protocol_name)
        if not protocol_class:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        return protocol_class()
