# CS262 Chat Application

Welcome to our chat app, a PyQt6-based client with a dark theme UI and a Python server for real-time messaging!

Our application is built with a client-server architecture, supporting multiple clients connecting to the server from different machines. We have implemented two **wire protocols**: JSON and our custom protocol (SAMIRA🔥).

[![Design Documentation](https://img.shields.io/badge/Design-Documentation-blue)](/design/DESIGN_DOC.md) [![Client Documentation](https://img.shields.io/badge/Client-Documentation-blue)](src/client/README.md) [![Server Documentation](https://img.shields.io/badge/Server-Documentation-blue)](src/server/README.md) [![Protocol Documentation](https://img.shields.io/badge/Protocol-Documentation-blue)](src/protocol/README.md)

[![Test Suite & Coverage Status](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml/badge.svg)](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml)

## Features

Our application implements the below functional requirements:

✅ **Account Management**

- Create account with unique username, nickname, and password
- Log in with existing account
- Delete account
- List/search accounts with wildcard support

✅ **Messaging**

- Real-time message delivery
- Offline message storage
- Configurable unread message to be delivered at any time
- Message status tracking (number of unread messages)
- Individual and bulk message deletion

✅ **Multi-Machine Support**

- Tested server-client communication on different machines
- Server accessible from any client on the network
- Tested with two **wire protocols**: JSON and our custom protocol (SAMIRA🔥)

For more details on features, high-level design, and implementation, see our [High-Level Design & Implementation Plan](/design/DESIGN_DOC.md).

## Demo
<!-- TODO: [View Demo GIFs showing multi-machine usage](#demo-gifs) -->
<details>
  <summary><strong><span style="font-size: 2em;"> Open Me! 🎬 </span></strong></summary>
   
https://github.com/user-attachments/assets/23159f82-a360-44ae-9f69-68630fd223f8

https://github.com/user-attachments/assets/79279374-0d96-4468-a49f-0a8b925eca22

https://github.com/user-attachments/assets/90902194-2182-40e5-b5b0-f3dc60822fd2

https://github.com/user-attachments/assets/4c007c8a-32b3-4ade-a0ac-e5670e87555d

https://github.com/user-attachments/assets/b0ac3eb2-e144-4800-b412-a0a5f059d8a0

https://github.com/user-attachments/assets/cce96add-d02c-4c67-b1b2-f980f0db6108

</details>

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- make (build tool)

### Quick Start

1. Clone and install:

```bash
git clone https://github.com/yourusername/cs262-chat.git
cd cs262-chat
make install && make install-dev
```

2. Start server:

```bash
make run-server
```

3. Start client

   1. On the same machine as server (new terminal):

      ```bash
      make run-client-gui
      ```

   2. Connecting from a different machine (replace `SERVER_IP` with server's IP):

      ```bash
      make run-client-gui CLIENT_ID=YOUR_DESIRED_ID SERVER_IP=SERVER_IP
      ```

> [!NOTE]
> > `SERVER_IP` will be displayed on the machine where the server is running with other server details (e.g. what wire protocol is being used, port, etc.).
> `YOUR_DESIRED_ID` can be any string you want to use as your client ID.

## Documentation Structure

Our documentation is organized for easy navigation:

- **[Client Documentation](src/client/README.md)**

  PyQt6-based GUI application covering:

  - UI components and pages
  - Implements our [User journey diagrams](/design/user_journey_ui.drawio.png)
  - Client code communication with server

- **[Server Documentation](src/server/README.md)**

  - API endpoints
  - Database schema
  - Server setup code

- **[Protocol Documentation](src/protocol/README.md)**
  - Wire protocol specifications
  - Message format details
  - Protocol Implementation (JSON vs Custom)

> [!NOTE]
> **Engineering Notebook**
> For our other documents, especially engineering notebooks, see the [notebook.md](./design/notebook.md) file and the [Issues Page](https://github.com/mirabor/cs262-chat/issues?q=is%3Aissue%20state%3Aclosed)

## Testing Coverage

Our test suite coverage report can be found by clicking on the badge below:

[![Test Suite & Coverage Status](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml/badge.svg)](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml)

Also, you can run the test suite locally with:

```bash
make test
```

## Project Structure

```bash
.
├── Makefile
├── design/
├── src/
│   ├── client/         # Client-side & UI implementation
│   │   ├── components
│   │   └── pages
│   ├── protocol/       # Protocol definitions and handlers
│   └── server/         # Server-side implementation
└── tests
    ├── client
    ├── protocol
    └── server
```

## Development

### Code Style

- Follows PEP 8 guidelines
- Auto-formatting available:

```bash
make fix-style
```

> [!TIP]
> For other development `make` commands, simply run `make` to see the available options.
