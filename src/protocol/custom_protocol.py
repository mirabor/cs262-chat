import struct
from typing import Any, Tuple
from .message_protocol import MessageProtocol


class CustomProtocol(MessageProtocol):
    """A custom binary protocol implementation

    Type Tags (1 byte):
    - 0x01: String (2-byte length + UTF-8 bytes)
    - 0x02: Integer (4 bytes, signed, big-endian)
    - 0x03: Float (8 bytes, double precision)
    - 0x04: Boolean (1 byte: 0x00=False, 0x01=True)
    - 0x05: Null (no additional data)
    - 0x06: Array (4-byte length + items)
    - 0x07: Object/Dict (4-byte pair count + key-value pairs)

    All multi-byte numbers are encoded in network byte order (big-endian).
    """

    # Type tags
    TYPE_STRING = 0x01
    TYPE_INT = 0x02
    TYPE_FLOAT = 0x03
    TYPE_BOOL = 0x04
    TYPE_NULL = 0x05
    TYPE_ARRAY = 0x06
    TYPE_DICT = 0x07

    def serialize(self, message: dict) -> bytes:
        """Serialize a dictionary into binary format.

        Raises:
            ValueError: If message is not a dictionary or contains unsupported types
        """
        if not isinstance(message, dict):
            raise ValueError("Top-level message must be a dictionary")

        return self._serialize_dict(message)

    def deserialize(self, data: bytes) -> dict:
        """Deserialize binary data back into a dictionary.

        Raises:
            ValueError: If data is malformed or incomplete
        """
        if not data:
            raise ValueError("Empty input")

        try:
            value, remaining = self._deserialize_value(data)
            if remaining:  # Extra data after valid message
                raise ValueError("Extra data after message")
            if not isinstance(value, dict):
                raise ValueError("Top-level data must be a dictionary")
            return value
        except struct.error as e:
            raise ValueError(f"Malformed binary data: {str(e)}") from e

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize a single value with its type tag."""
        if isinstance(value, str):
            encoded = value.encode("utf-8")
            return bytes([self.TYPE_STRING]) + struct.pack(">I", len(encoded)) + encoded
        elif isinstance(value, int):
            return bytes([self.TYPE_INT]) + struct.pack(">i", value)
        elif isinstance(value, float):
            return bytes([self.TYPE_FLOAT]) + struct.pack(">d", value)
        elif isinstance(value, bool):
            return bytes([self.TYPE_BOOL, 1 if value else 0])
        elif value is None:
            return bytes([self.TYPE_NULL])
        elif isinstance(value, list):
            return self._serialize_array(value)
        elif isinstance(value, dict):
            return self._serialize_dict(value)
        else:
            raise ValueError(f"Unsupported type: {type(value)}")

    def _serialize_array(self, arr: list) -> bytes:
        """Serialize an array."""
        result = bytes([self.TYPE_ARRAY]) + struct.pack(">I", len(arr))
        for item in arr:
            result += self._serialize_value(item)
        return result

    def _serialize_dict(self, d: dict) -> bytes:
        """Serialize a dictionary."""
        result = bytes([self.TYPE_DICT]) + struct.pack(">I", len(d))
        for key, value in d.items():
            if not isinstance(key, str):
                raise ValueError("Dictionary keys must be strings")
            key_bytes = key.encode("utf-8")
            result += struct.pack(">H", len(key_bytes)) + key_bytes
            result += self._serialize_value(value)
        return result

    def _deserialize_value(self, data: bytes) -> Tuple[Any, bytes]:
        """Deserialize a value and return it plus remaining data."""
        if not data:
            raise ValueError("Incomplete message")

        type_tag = data[0]
        data = data[1:]

        if type_tag == self.TYPE_STRING:
            if len(data) < 4:
                raise ValueError("Incomplete string length")
            length = struct.unpack(">I", data[:4])[0]
            data = data[4:]
            if len(data) < length:
                raise ValueError("Incomplete string data")
            return data[:length].decode("utf-8"), data[length:]

        elif type_tag == self.TYPE_INT:
            if len(data) < 4:
                raise ValueError("Incomplete integer")
            return struct.unpack(">i", data[:4])[0], data[4:]

        elif type_tag == self.TYPE_FLOAT:
            if len(data) < 8:
                raise ValueError("Incomplete float")
            return struct.unpack(">d", data[:8])[0], data[8:]

        elif type_tag == self.TYPE_BOOL:
            if not data:
                raise ValueError("Incomplete boolean")
            return bool(data[0]), data[1:]

        elif type_tag == self.TYPE_NULL:
            return None, data

        elif type_tag == self.TYPE_ARRAY:
            return self._deserialize_array(data)

        elif type_tag == self.TYPE_DICT:
            return self._deserialize_dict(data)

        else:
            raise ValueError(f"Unknown type tag: {type_tag}")

    def _deserialize_array(self, data: bytes) -> Tuple[list, bytes]:
        """Deserialize an array and return it plus remaining data."""
        if len(data) < 4:
            raise ValueError("Incomplete array length")
        length = struct.unpack(">I", data[:4])[0]
        data = data[4:]

        result = []
        for _ in range(length):
            value, data = self._deserialize_value(data)
            result.append(value)
        return result, data

    def _deserialize_dict(self, data: bytes) -> Tuple[dict, bytes]:
        """Deserialize a dictionary and return it plus remaining data."""
        if len(data) < 4:
            raise ValueError("Incomplete dictionary length")
        length = struct.unpack(">I", data[:4])[0]
        data = data[4:]

        result = {}
        for _ in range(length):
            # Read key
            if len(data) < 2:
                raise ValueError("Incomplete key length")
            key_len = struct.unpack(">H", data[:2])[0]
            data = data[2:]
            if len(data) < key_len:
                raise ValueError("Incomplete key data")
            key = data[:key_len].decode("utf-8")
            data = data[key_len:]

            # Read value
            value, data = self._deserialize_value(data)
            result[key] = value

        return result, data
