# Protocol Implementation Documentation

## Architecture Overview

### 1. Protocol Factory Pattern (`protocol_factory.py`)

The protocol layer is implemented using the Factory pattern to allow testing with multiple serialization protocols:

```python
MessageProtocol (ABC)
├── JsonProtocol
└── CustomProtocol (TODO:)
```

- **MessageProtocol**: Abstract base class defining the protocol interface

  - `serialize(message: dict) -> bytes`: Convert messages to bytes
  - `deserialize(data: bytes) -> dict`: Convert bytes back to messages

- **JsonProtocol**: Default implementation using JSON serialization
- **CustomProtocol**: Placeholder for our custom protocol implementation (TODO:)

### 2. Server Implementation (`server.py`)

The server uses a multi-threaded architecture for handling concurrent clients:

- **Main Thread**: Accepts new connections
- **Client Threads**: One per connected client
  - Handles client messages
  - Manages client lifecycle
  - Stores messages

Key features:

- Thread-safe client management using locks
- Configurable maximum client limit (TODO: what happens when the limit is reached?)

### 3. Client Implementation (`client.py`)

Single-threaded client with the following features:

- Unique client identification
- Connection management
- Message sending/receiving

### 4. Configuration Management (`config_manager.py`)

YAML-based configuration system managing:

- Network settings (host, port)
- Protocol selection
- Client limits
- Buffer sizes
- Message storage paths

## Message Flow

1. **Connection Establishment**:

   ```
   Client                     Server
     │                           │
     ├─── connection_request ───▶│
     │                           │
     │◀── connection_response  ──┤
   ```

2. **Message Exchange**:
   ```
   Client                     Server
     │                          │
     ├─── client_message ─────▶ │
     │                          ├─► Store Message
     │◀── delivery_status  ─────┤
   ```

## Protocol Extension

To implement a new protocol:

1. Create a new class implementing `MessageProtocol`
2. Implement `serialize()` and `deserialize()` methods
3. Register with `ProtocolFactory`:
   ```python
   ProtocolFactory.register_protocol("new_protocol", NewProtocolClass)
   ```

## Error Handling

The implementation includes error handling for:

- Connection failures
- Protocol errors
- Client disconnections
- Message delivery failures

## Thread Safety Considerations

- Server uses threading.Lock for client list access
- Message storage operations are atomic
- Socket operations are thread-safe by design

## Debugging Tips

1. Enable debug logging in config:

   ```yaml
   debug: true
   log_level: DEBUG
   ```

2. Monitor client connections:

   ```bash
   lsof -i :5555  # Check port usage
   ```

3. Test protocol implementation:
   ```python
   protocol = ProtocolFactory.get_protocol("json")
   test_msg = {"type": "test", "data": "hello"}
   assert protocol.deserialize(protocol.serialize(test_msg)) == test_msg
   ```
