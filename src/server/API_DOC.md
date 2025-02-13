# API Documentation

## Endpoints

### 1. Authentication

#### Sign Up

Creates a new user account.

**Request Body:**

```json
{
  "username": "john_harvard",
  "nickname": "John",
  "password": "securepassword123"
}
```

**Response:**

```json
{
  "success": true,
  "error_message": ""
}
```

#### Login

Authenticates a user.

**Request Body:**

```json
{
  "username": "john_harvard",
  "password": "securepassword123"
}
```

**Response:**

TODO:

### 2. Chat Management

#### Get Chats

Retrieves all necessary chat information for displaying the chat list UI.

**Parameters:**

- `user_id` (required): Integer ID of the user whose chats are being retrieved

**Response:**

```json
{
  "success": true,
  "chats": [
    {
      "chat_id": "1some_id2",
      "other_user": "username",
      "unread_count": 5 // Number of unread messages
    }
  ],
  "error": null // null if successful, error message if failed
}
```

### 3. Message Management

#### Send Message

Sends a new message
TODO:

#### Delete Messages

Delete user and all his settings (no recovery, delete means delete forever).
TODO: should we delete all chats they are involved in??

#### Get Chat Messages

Retrieves messages for a specific chat. If the retriever is the `receiver` all the
unread messages will automatically be marked as read. Intuitively it'd make more sense to have client request to mark messages as read, after they're displayed... but for simplicity, we let the server handle it here.

**Parameters**

```json
{
  "action": "get_messages",
  "chat_id": "chat_id",
  "current_user": "current_user"
}
```

**Output**

```json
{
  "success": true,
  "messages": {
    "id": "some_id",
    "sender": "username"
    "receiver": "username.",
    "content": "...",
    "timestamp": "...",
    "read": 1
  },
  "error_message": ""
}
```

### 4. User Management

#### Delete Account

Deletes a user account. TODO: should we delete all chats or just account? Tradeoffs?

**Response:**

```json
{
  "success": true,
  "error_message": ""
}
```

#### Update Settings

Updates user settings, currently number of messages that can be delivered at any time `message_limit`.

TODO:

#### Get Message Limit

TODO:

#### Get Users List

TODO:
