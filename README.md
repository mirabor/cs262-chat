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

## System Design and Implementation

### Wire Protocols

Custom Protocol: Designed for efficiency, our protocol minimizes the size of the data transmitted over the network. It uses binary encoding for messages and it's optimized for low latency and high throughput.

JSON Protocol: This protocol uses JSON for message serialization. It's easier to debug and human-readable,  development and testing.

## Requirements

### 1. **Creating an Account**
- **Description**: Users can create an account by providing a unique username and password. The password is hashed before transmission to ensure security.
- **Implementation**:
  - **Client**: The `signup_page.py` file handles the UI for account creation and sends the request to the server.
  - **Server**: The `api.py` file processes the account creation request, checks for username availability, and stores the hashed password in the database (`chat_app.db`).
  - **Database**: The `db_manager.py` file manages user data storage and retrieval.
- **Files**:
  - `src/client/pages/signup_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 2. **Logging In to an Account**
- **Description**: Users can log in using their username and password. The server verifies the credentials and returns the number of unread messages.
- **Implementation**:
  - **Client**: The `login_page.py` file handles the login UI and sends the credentials to the server.
  - **Server**: The `api.py` file verifies the credentials and retrieves the number of unread messages from the database.
  - **Database**: The `db_manager.py` file handles credential verification and message count retrieval.
- **Files**:
  - `src/client/pages/login_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 3. **Listing Accounts**
- **Description**: Users can list all accounts or filter them using a wildcard pattern. The system supports scrolling pagination for large lists.
- **Implementation**:
  - **Client**: The `users_page.py` file handles the UI for listing accounts and sends the filter request to the server.
  - **Server**: The `api.py` file processes the request and retrieves the list of accounts from the database.
  - **Database**: The `db_manager.py` file handles the query and pagination logic.
- **Files**:
  - `src/client/pages/users_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 4. **Sending a Message**
- **Description**: Users can send messages to other users. If the recipient is offline, the message is stored until they log in. Messages will deliver immediately if the recipient is logged in and will dynamically update if two users are chatting at the same time. In order to update a user's home page with new messages, they can simply click any button to refresh, including the Home button.
- **Implementation**:
  - **Client**: The `chat_page.py` file handles the UI for composing and sending messages.
  - **Server**: The `api.py` file processes the message and checks the recipient's status. If the recipient is offline, the message is stored in the database.
  - **Database**: The `db_manager.py` file manages message storage and retrieval.
- **Files**:
  - `src/client/pages/chat_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 5. **Reading Messages**
- **Description**: Users can read their messages. The system allows users to specify the number of messages that are "delivered" as unread messages to the user's home page at once to avoid overwhelming the client. Once users open a chat, those messages are "read", and the new, unread messages (up to the limit specified) will display if the user navigates back to the home page and requests to see their messages again. 
- 
- **Implementation**:
  - **Client**: The `chat_page.py` and `settings_page.py` files handles the UI for displaying messages and allowing users to specify the number of unread messages to display at once.
  - **Server**: The `api.py` file processes the request and retrieves the specified number of messages from the database.
  - **Database**: The `db_manager.py` file handles message retrieval and marking messages as read.
- **Files**:
  - `src/client/pages/chat_page.py`
  - `src/client/pages/settings_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 6. **Deleting Messages**
- **Description**: Users can delete individual messages or a set of messages. Deleted messages are removed from both the client and server.
- **Implementation**:
  - **Client**: The `chat_page.py` file handles the UI for deleting messages.
  - **Server**: The `api.py` file processes the deletion request and removes the messages from the database.
  - **Database**: The `db_manager.py` file handles message deletion.
- **Files**:
  - `src/client/pages/chat_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`

### 7. **Deleting an Account**
- **Description**: Users can delete their accounts. The system specifies the behavior for accounts with unread messages (e.g., notify the user before deletion).
- **Implementation**:
  - **Client**: The `settings_page.py` file handles the UI for account deletion.
  - **Server**: The `api.py` file processes the deletion request and removes the account and associated messages from the database.
  - **Database**: The `db_manager.py` file handles account and message deletion.
- **Files**:
  - `src/client/pages/settings_page.py`
  - `src/server/api.py`
  - `src/server/db_manager.py`


## Initial Design Diagram

![user_journey_ui drawio](https://github.com/user-attachments/assets/a4a1ac9a-180a-48af-b188-3a179f9b6674)

