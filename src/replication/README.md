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