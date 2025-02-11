from typing import Type
from .message_protocol import MessageProtocol
from .custom_protocol import CustomProtocol
import json


class JsonProtocol(MessageProtocol):
    def serialize(self, message: dict) -> bytes:

        if not isinstance(message, dict):
            raise ValueError("Input must be a dictionary")

        try:
            return json.dumps(message).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize to JSON: {str(e)}") from e

    def deserialize(self, data: bytes) -> dict:
        """Deserialize JSON-encoded bytes back into a dictionary."""
        if not data:
            raise ValueError("Empty input")

        try:
            # First decode bytes to string, handling UTF-8 errors
            try:
                str_data = data.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError("Invalid UTF-8 encoding") from e

            # Parse JSON
            parsed = json.loads(str_data)

            # Validate that result is a dictionary/object
            if not isinstance(parsed, dict):
                raise ValueError("JSON must be an object/dictionary")

            # Check for invalid JavaScript values
            def validate_values(obj):
                if isinstance(obj, dict):
                    for _, value in obj.items():
                        validate_values(value)
                elif isinstance(obj, list):
                    for item in obj:
                        validate_values(item)

            validate_values(parsed)

            return parsed

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}") from e


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
