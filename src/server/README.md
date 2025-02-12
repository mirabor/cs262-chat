# Server Application

This is the server-side implementation of our chat app, which provides real-time chat functionality and user management.

## Structure

```
src/server/
├── __init__.py
├── config_manager.py    # Server configuration management
├── db_manager.py        # Database operations and management
├── main.py             # Server entry point
├── server.py           # Core server implementation
└── utils.py            # Utility functions
```

## Key Components

### Core Files

- `main.py`: Server entry point that initializes the server and starts listening for connections
- `server.py`: Core server implementation handling client connections, message routing, and chat management
- `db_manager.py`: SQLite database interface for persistent storage of users, chats, and messages
- `config_manager.py`: Manages server configuration including network settings and database options

### Features

- Real-time message delivery
- User authentication and session management
- Persistent chat history
- Message status tracking (sent, delivered, read)
- Configurable message retention and view limits
- Support for multiple chat protocols (JSON, Custom)

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

The server can be configured through a JSON configuration file with the following options:

```json
{
    "network": {
        "host": "localhost",
        "port": 8000,
        "protocol": "json",
        "max_clients": 100,
        "message_buffer_size": 2048
    },
    "database": {
        "path": "chat_app.db",
        "default_view_limit": 50,
        "message_retention_days": 30
    },
    "security": {
        "min_password_length": 8,
        "max_login_attempts": 3,
        "session_timeout_minutes": 60
    }
}
```

## Development

Our design choices included:

- Clean separation of concerns between components
- Protocol-agnostic message handling
- Efficient database operations
- Robust error handling and logging
- Configurable settings for different deployment scenarios

### Adding New Features

1. For new message types, update the message handling in `server.py`
2. For new database operations, add them to `db_manager.py`
3. For new configuration options, update `config_manager.py`
4. Ensure proper error handling and logging

### Testing

Tests for the server application can be found in the `tests/server/` directory.
