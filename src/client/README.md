# Client Application

This directory contains the client-side implementation of our chatApp built with PyQt6.

## Structure

```
src/client/
├── components/         # Reusable UI components
├── pages/             # Individual application pages/screens
├── __init__.py
├── client.py          # Network client implementation
├── logic.py           # Business logic layer             TODO: to be combined w/ client.py
├── main.py           # Application entry point
├── ui.py             # Main window and UI orchestration
├── utils.py          # Utility functions
├── chats.json        # Local chat history storage        TODO: To be removed
└── users.json        # Local user data storage          TODO: To be removed
```

## Key Components

### Core Files

- `main.py`: Application entry point that initializes the PyQt application
- `ui.py`: Main window implementation with dark theme styling and page management
- `logic.py`: Business logic for chat operations, user management, and application state
- `client.py`: Handles network communication with the chat server

### UI Components

- `pages/`: Contains different screens of the application:
  - `HomePage`: Main landing page
  - `ChatPage`: Chat interface
  - `LoginPage`: User authentication
  - `UsersPage`: User management
  - `SignupPage`: New user registration
  - `SettingsPage`: Application settings

## Getting Started

1. Install dependencies:

```bash
make install
```

2. Run the application:

```bash
make run-client-gui
```

TODO: To be updated `make run-client` once it can communicate to the server.

## Development

The application follows these design principles:

- Modular architecture with clear separation of concerns
- Separation of UI logic from business logic
- Component-based UI design using PyQt6
- Dark theme by default for better user experience

### Adding New Features

1. For new UI components, add them to the `components/` directory
2. For new screens, create them in the `pages/` directory
3. Update `ui.py` to integrate new pages into the navigation system
4. Add business logic in `logic.py`
5. Update data models in `client.py` if needed

### Testing

Tests for the client application can be found in the `tests/client/` directory.
