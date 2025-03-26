# CS262 Chat Application

Welcome to our chat app, a PyQt6-based client with a dark theme UI and a Python server for real-time messaging!

Our application is built with a client-server architecture, supporting multiple clients connecting to the server from different machines. We have implemented two wire protocols: JSON and our custom protocol (SAMIRA🔥), as well as a fault-tolerant replication system using gRPC for server-to-server communication.

[![Design Documentation](https://img.shields.io/badge/Design-Documentation-blue)](/design/DESIGN_DOC.md) [![Client Documentation](https://img.shields.io/badge/Client-Documentation-blue)](src/client/README.md) [![Server Documentation](https://img.shields.io/badge/Server-Documentation-blue)](src/server/README.md) [![Protocol Documentation](https://img.shields.io/badge/Protocol-Documentation-blue)](src/protocol/README.md) [![Replication Documentation](https://img.shields.io/badge/Replication-Documentation-blue)](src/replication/README.md) 

[![Test Suite & Coverage Status](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml/badge.svg)](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml)

<details>
  <summary><h2>Features</h2></summary>

Our application implements the below functional requirements:

- [x] **Account Management**

- Create account with unique username, nickname, and password
- Log in with existing account
- Delete account
- List/search accounts with wildcard support

- [x] **Messaging**

- Real-time message delivery
- Offline message storage
- Configurable unread message to be delivered at any time
- Message status tracking (number of unread messages)
- Individual and bulk message deletion

- [x] **Multi-Machine Support**

- Tested server-client communication on different machines
- Server accessible from any client on the network
- Tested with two **wire protocols**: JSON and our custom protocol (SAMIRA🔥)

- [x] **Fault-Tolerant Replication**

- Raft-inspired leader election protocol
- 2-fault tolerant server cluster
- Automatic failover with leader election
- Dynamic server addition to the replica set
- gRPC-based server-to-server communication

For more details on features, high-level design, and implementation, see our [High-Level Design & Implementation Plan](/design/DESIGN_DOC.md).

</details>


<details>
  <summary><h2>Getting Started</h2></summary>

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
# Standard mode (single server)
make run-server

# Fault-tolerant mode with gRPC replication
# Start first server (leader)
make run-server MODE=grpc SERVER_ID=server1 PORT=5555

# Add additional replicas
make run-server MODE=grpc SERVER_ID=server2 PORT=5556 PEERS=localhost:5555
make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=localhost:5555,localhost:5556
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

</details>

> [!NOTE]
> > `SERVER_IP` will be displayed on the machine where the server is running with other server details (e.g. what wire protocol is being used, port, etc.).
> `YOUR_DESIRED_ID` can be any string you want to use as your client ID.


<details>
  <summary><h2>Documentation Structure</h2></summary>

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

- **[Replication Documentation](src/replication/README.md)**
  - Fault-tolerant architecture
  - Raft-inspired leader election
  - Server-to-server communication
  - Testing instructions

</details>

> [!NOTE]
> **Engineering Notebook**
> For our other documents, especially engineering notebooks, see the [notebook.md](./design/notebook.md) file and the [Issues Page](https://github.com/mirabor/cs262-chat/issues?q=is%3Aissue%20state%3Aclosed)


<details>
  <summary><h2>Testing Coverage</h2></summary>

Our test suite coverage report can be found by clicking on the badge below:

[![Test Suite & Coverage Status](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml/badge.svg)](https://github.com/mirabor/cs262-chat/actions/workflows/test.yml)

Also, you can run the test suite locally with:

```bash
make test
```

</details>

<details>
  <summary><h2>Project Structure</h2></summary>

![image](https://github.com/user-attachments/assets/428fda87-5ae3-4445-89f9-a48ab46efcd8)

```bash
├── Makefile
├── design/
│   ├── notebook.md
│   ├── replicas-notebook.md
│   └── wire-protocol-notebook.md
├── src/
│   ├── client/
│   │   ├── components/
│   │   └── pages/
│   ├── protocol/ # Protocol definitions and handlers
│   │   ├── grpc/
│   │   │   ├── chat_pb2.py
│   │   │   ├── chat_pb2_grpc.py
│   │   │   ├── replication_pb2.py
│   │   │   └── replication_pb2_grpc.py
│   │   ├── json/
│   │   └── samira/   # (custom impl, samira)
│   ├── replication/
│   │   ├── config.py
│   │   ├── election_manager.py
│   │   ├── heartbeat_manager.py
│   │   ├── replica_node.py 
│   │   ├── replica_state.py
│   │   └── replication_manager.py
│   └── server/
└── tests/
    ├── client/
    ├── protocol/
    ├── replication/
    └── server/
```

</details>

<details>
  <summary><h2>Problem 1 Demo</h2></summary>
<!-- TODO: [View Demo GIFs showing multi-machine usage](#demo-gifs) -->
   
https://github.com/user-attachments/assets/23159f82-a360-44ae-9f69-68630fd223f8

https://github.com/user-attachments/assets/79279374-0d96-4468-a49f-0a8b925eca22

https://github.com/user-attachments/assets/90902194-2182-40e5-b5b0-f3dc60822fd2

https://github.com/user-attachments/assets/4c007c8a-32b3-4ade-a0ac-e5670e87555d

https://github.com/user-attachments/assets/b0ac3eb2-e144-4800-b412-a0a5f059d8a0

https://github.com/user-attachments/assets/cce96add-d02c-4c67-b1b2-f980f0db6108

</details>

<details>
  <summary><h2>Development</h2></summary>

### Code Style

- Follows PEP 8 guidelines
- Auto-formatting available:

```bash
make fix-style
```

</details>

> [!TIP]
> For other development `make` commands, simply run `make` to see the available options.
