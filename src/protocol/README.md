# Custom Wire Protocol (SAMIRA 🔥) Design

## Overview

This describes our custom wire protocol implementation used in our chat application. The protocol is designed to be efficient than JSON while maintaining support for complex data structures.

## Design Goals

1. **Efficiency**: Minimize message size compared to text-based formats
2. **Flexibility**: Support all JSON-like data structures
3. **Robustness**: Handle errors gracefully and provide clear error messages
4. **Simplicity**: Keep the implementation straightforward and maintainable

## Protocol Specification

### Type System

Each value is prefixed with a 1-byte type tag:

| Tag  | Type    | Format                              | Example Use Case |
| ---- | ------- | ----------------------------------- | ---------------- |
| 0x01 | String  | 4-byte length + UTF-8 bytes         | Message content  |
| 0x02 | Integer | 4 bytes, signed, big-endian         | User IDs         |
| 0x03 | Float   | 8 bytes, double precision           | Timestamps       |
| 0x04 | Boolean | 1 byte (0x00=False, 0x01=True)      | Status flags     |
| 0x05 | Null    | No additional data                  | Optional fields  |
| 0x06 | Array   | 4-byte length + items               | Message lists    |
| 0x07 | Dict    | 4-byte pair count + key-value pairs | Message objects  |

### Message Format

Top-level messages must be dictionaries with the following structure:

```
[0x07][4-byte pair count][
    [2-byte key length][key bytes][value with type tag]
    ...
]
```

### String Encoding

- Strings use a 4-byte length prefix to support messages up to 4GB
- UTF-8 encoding ensures proper handling of Unicode characters
- No null termination needed due to explicit length

### Number Encoding

- Integers: 4-byte signed, supporting range -2³¹ to 2³¹-1
- Floats: 8-byte
- All multi-byte numbers use network byte order (big-endian)

## Implementation Notes

### Error Handling

The implementation includes robust error checking for:

- Incomplete messages
- Invalid UTF-8 encoding
- Unknown type tags
- Buffer overruns
- Type mismatches
- Malformed data

### Testing

Comprehensive test suite covers:

- All data types
- Nested structures
- Edge cases (empty, very large)
- Error conditions
- Round-trip serialization

## Usage Example

```python
from protocol import CustomProtocol

protocol = CustomProtocol()

# Serialize
message = {
    "type": "chat_message",
    "content": "Hello, world!",
    "timestamp": 1644582794.123
}
binary_data = protocol.serialize(message)

# Deserialize
decoded = protocol.deserialize(binary_data)
assert decoded == message
```

## Future Improvements

1. **Schema Validation**: Add optional schema validation
2. **Compression**: Implement optional message compression
3. **Versioning**: Add protocol version negotiation
4. ...
