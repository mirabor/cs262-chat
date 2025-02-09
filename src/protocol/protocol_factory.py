from abc import ABC, abstractmethod
import json
import struct


class MessageProtocol(ABC):
    @abstractmethod
    def serialize(self, message: dict) -> bytes:
        """Convert a message dictionary to bytes for transmission"""
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> dict:
        """Convert received bytes back to a message dictionary"""
        pass


class JsonProtocol(MessageProtocol):
    def serialize(self, message: dict) -> bytes:
        return json.dumps(message).encode()

    def deserialize(self, data: bytes) -> dict:
        return json.loads(data.decode())


class CustomProtocol(MessageProtocol):
    def serialize(self, message: dict) -> bytes:
        # TODO:
        raise NotImplementedError("Custom serialization not implemented")

    def deserialize(self, data: bytes) -> dict:
        # TODO:
        raise NotImplementedError("Custom deserialization not implemented")


class ProtocolFactory:
    _protocols = {"json": JsonProtocol, "custom": CustomProtocol}

    @classmethod
    def register_protocol(cls, name: str, protocol_class: MessageProtocol):
        cls._protocols[name] = protocol_class

    @classmethod
    def get_protocol(cls, protocol_name: str) -> MessageProtocol:
        protocol_class = cls._protocols.get(protocol_name)
        if not protocol_class:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        return protocol_class()
