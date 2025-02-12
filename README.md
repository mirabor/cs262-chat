# CS262 Chat Application

Our chat app consists of a PyQt6-based client with a dark theme UI and a robust Python server supporting real-time messaging.

## Project Structure

```
.
├── src/
│   ├── client/          # Client-side implementation
│   ├── protocol/        # Protocol definitions and handlers
│   └── server/          # Server-side implementation
├── tests/               # Test suites
├── requirements.txt     # Python dependencies
└── Makefile            # Build and run commands
```

## Features

- Real-time messaging with message status tracking
- User authentication and account management
- Dark mode UI
- Multiple chat protocols support (JSON, our custom protocol)
- Persistent chat history
- Marking messages as read/unread
- User search filtering
- Configurable message view limits
- Robust error handling

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- make (build tool)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cs262-chat.git
cd cs262-chat
```

2. Install dependencies:
```bash
make install && make install-dev
```

### Running the Application

1. Start the server:
```bash
make run-server
```

2. Start the client (in a new terminal):
```bash
make run-client-gui
```

## Development

### Project Components

- **Client**: PyQt6-based GUI application ([documentation](src/client/README.md))
- **Server**: Python-based chat server ([documentation](src/server/README.md))
- **Protocol**: Message protocol implementations ([documentation](src/protocol/README.md))

### Running Tests

```bash
make test
```

### Code Style

This project follows PEP 8 style guidelines. Format your code using:

```bash
make format
```
