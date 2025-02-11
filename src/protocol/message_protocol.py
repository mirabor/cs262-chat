from abc import ABC, abstractmethod


class MessageProtocol(ABC):
    @abstractmethod
    def serialize(self, message: dict) -> bytes:
        """
        Convert a message dictionary to bytes for transmission.
        :param message: The message as a dictionary.
        :return: The serialized message as bytes.
        """
        pass

    @abstractmethod
    def deserialize(self, data: bytes) -> dict:
        """
        Convert received bytes back to a message dictionary.
        :param data: The received bytes.
        :return: The deserialized message as a dictionary.
        """
        pass
