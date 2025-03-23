# Server Application

This is the server-side implementation of our chat app, which provides real-time chat functionality and user management.

## Structure

```
src/server/
├── APL_DOC.md
├── db_manager.py
├── grpc_server.py
├── main.py
├── README.md
├── tcp_server.py
```

## Key Components

### Core Files

- `main.py`: Server entry point that initializes the server and starts listening for connections.
- `grpc_server.py`: gRPC server implementation for handling gRPC-based client connections.
- `tcp_server.py`: TCP server implementation for handling TCP-based client connections.
- `db_manager.py`: SQLite database interface for persistent storage of users, chats, and messages.

### Features

- Real-time message delivery.
- User authentication and session management.
- Persistent chat history.
- Message status tracking (sent, delivered, read).
- Configurable message retention and view limits.
- Support for multiple chat protocols (gRPC, TCP, JSON)

## Getting Started

1. Install dependencies:

```bash
make install
```

2. Run the server:

```bash
make run-server
```

## Configuration

The server can be configured through a YAML configuration file with the following options:

```yaml
network:
  buffer_size: 1024
  connection_timeout: 10
  host: 0.0.0.0
  max_clients: 10
  messages_dir: client_messages
  port: 5555
  protocol: custom
  retry_attempts: 3
  retry_delay: 2
```

### Configuration Options

- `buffer_size`: The size of the buffer used for message transmission.
- `connection_timeout`: The timeout duration for client connections in seconds.
- `host`: The host address the server will bind to (e.g., `0.0.0.0` for all interfaces).
- `max_clients`: The maximum number of clients that can connect to the server simultaneously.
- `messages_dir`: The directory where client messages are stored.
- `port`: The port number the server will listen on.
- `protocol`: The communication protocol used (e.g., `custom`, `json`, `grpc`).
- `retry_attempts`: The number of retry attempts for failed operations.
- `retry_delay`: The delay between retry attempts in seconds.

## Development

Our design choices included:

- Clean separation of concerns between components.
- Protocol-agnostic message handling.
- Efficient database operations.
- Robust error handling and logging.
- Configurable settings for different deployment scenarios.

### Adding New Features

1. For new message types, update the message handling in `grpc_server.py` or `tcp_server.py`.
2. For new database operations, add them to `db_manager.py`.
3. For new configuration options, update the YAML configuration file.
4. Ensure proper error handling and logging.

### Testing

Tests for the server application can be found in the `tests/server/` directory.
