from abc import ABC, abstractmethod
from enum import Enum, auto


class MessageProtocol(ABC):
    """
    Abstract base class for message protocols.

    To be extended by JsonProtocol and our CustomProtocol classes
    and define how messages are serialized and deserialized.
    """

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


class MessageType(Enum):
    # System messages
    CONNECT = auto()
    DISCONNECT = auto()
    ERROR = auto()

    # Auth messages
    LOGIN_REQUEST = auto()
    LOGIN_RESPONSE = auto()
    SIGNUP_REQUEST = auto()
    SIGNUP_RESPONSE = auto()

    # Chat messages
    CHAT_START = auto()
    CHAT_MESSAGE = auto()
    DELETE_MESSAGES = auto()
    DELETE_CHAT = auto()

    # User operations
    GET_USERS = auto()
    USER_LIST = auto()
    UPDATE_SETTINGS = auto()
    DELETE_ACCOUNT = auto()
