# Checklist
- [x] Multiple processes, multiple machines
- [x] Can fail any two servers and continue to function
- [x] Clear explanation as to how fail-over works in the code
- [x] Solid test suite
- [x] Documentation clear
- [x] Bonus: Can add a new server into its set of replicas (using make run-server, see test instructions below)

## How To Test

After installing all the requirements (e.x. `make install && make install-dev`) and loading the new environment (as detailed in root README.md), you can start the first replica by running: 

```bash
make run-server MODE=grpc SERVER_ID=server1 PORT=5555
```
This will start first server in the network/cluster. To add more server replicas (say 2), run: 

```bash
make run-server MODE=grpc SERVER_ID=server2 PORT=5556 PEERS=x.x.x.x:5555
```
where `x.x.x.x` is the address of the first server (e.x. "localhost" if on the same machine, the actual address if on separate machine). 
and
 
```bash
make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=x.x.x.x:5555,y.y.y.y:5556
```
where `y.y.y.y` is address of second replica. 

An example of last command can be something like: 

```bash
make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=10.250.10.214:5555,10.250.10.214:5556
```

# Replication System

```
┌─────────────────────────────────────────────────────────────────┐
│                       Replication System                         │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │  ReplicaNode  │    │  ReplicaNode  │    │  ReplicaNode  │    │
│  │   (Leader)    │◄───┤  (Follower)   │◄───┤  (Follower)   │    │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘    │
│          │                    │                    │            │
│          │    creates         │    creates         │    creates │
│          ▼                    ▼                    ▼            │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │ ReplicaState  │    │ ReplicaState  │    │ ReplicaState  │    │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘    │
│          │                    │                    │            │
│          │                    │                    │            │
│          ▼                    ▼                    ▼            │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │ElectionManager│    │ElectionManager│    │ElectionManager│    │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │HeartbeatManager│   │HeartbeatManager│   │HeartbeatManager│   │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │ReplicationManager│ │ReplicationManager│ │ReplicationManager│ │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **ReplicaNode**: Main entry point that:
   - Creates and initializes the ReplicaState
   - Creates ElectionManager and HeartbeatManager
   - Establishes cross-references between managers
   - Handles network joining and communication

2. **ReplicaState**: Central state container that:
   - Stores server identification (ID, address)
   - Tracks current term and role (leader/follower/candidate)
   - Maintains peer information and voting state
   - Is shared with both managers

3. **ElectionManager**: Election coordinator that:
   - Manages election timers
   - Handles vote solicitation and collection
   - Triggers state transitions based on election results
   - Uses the ReplicaState for decision making

4. **HeartbeatManager**: Communication handler that:
   - Sends heartbeats to followers (when leader)
   - Monitors leader liveness (when follower)
   - References the ElectionManager to trigger elections
   - Uses the ReplicaState to track peer status

## State Transition Diagram

```
┌────────────┐ timeout      ┌────────────┐ majority votes ┌────────────┐
│            │──────────────►            │───────────────►            │
│  Follower  │              │ Candidate  │               │   Leader   │
│            │◄─────────────┤            │◄──────────────┤            │
└────────────┘ higher term  └────────────┘  higher term  └────────────┘
      ▲                           │                            │
      │                           │                            │
      └───────────────────────────┴────────────────────────────┘
                            higher term
```

## Leader Election Process

1. **Initialization**: All nodes start as followers with random election timeouts

2. **Election Trigger**: A follower becomes candidate when:
   - No heartbeat received before timeout
   - Term is incremented
   - Votes for itself
   - Requests votes from peers

3. **Leadership**: A candidate becomes leader when:
   - It receives majority votes
   - Begins sending heartbeats
   - Coordinates all write operations

## Replication Flow

```
┌─────────┐    Write    ┌─────────┐  Replicate  ┌─────────┐
│ Client  │─────────────► Leader  │─────────────► Follower│
└─────────┘             └─────────┘             └─────────┘
                             │                       │
                             │                       │
                             ▼                       ▼
                        ┌─────────┐            ┌─────────┐
                        │ Apply   │            │ Apply   │
                        │ Changes │            │ Changes │
                        └─────────┘            └─────────┘
```

## Failure Handling

### Leader Failure
- Followers detect missing heartbeats
- New election starts after timeout
- New leader takes over

### Follower Failure
- Leader tracks missed acknowledgments
- Continues with remaining followers
- Rejoining followers catch up

## Config Parameters

- **ELECTION_TIMEOUT_MIN/MAX**: Random election timeout range
- **HEARTBEAT_INTERVAL**: Time between heartbeats
- **MAX_MISSED_HEARTBEATS**: Threshold for marking nodes as down