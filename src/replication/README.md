## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Replication System                         │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │  ReplicaNode  │    │  ReplicaNode  │    │  ReplicaNode  │    │
│  │   (Leader)    │◄───┤  (Follower)   │◄───┤  (Follower)   │    │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘    │
│          │                    │                    │            │
│          ▼                    ▼                    ▼            │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │ ReplicaState  │    │ ReplicaState  │    │ ReplicaState  │    │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│          │                    │                    │            │
│          ├────────────────────┼────────────────────┤            │
│          ▼                    ▼                    ▼            │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │ElectionManager│    │ElectionManager│    │ElectionManager│    │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│          │                    │                    │            │
│          ├────────────────────┼────────────────────┤            │
│          ▼                    ▼                    ▼            │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │HeartbeatManager    │HeartbeatManager    │HeartbeatManager    │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

1. **ReplicaNode**: Main entry point that manages:
   - Server state transitions
   - Communication between replicas
   - Election process
   - Data replication

2. **ReplicaState**: Maintains state information:
   - Server ID and address
   - Current term number
   - Current role (leader/follower/candidate)
   - Peer tracking

3. **ElectionManager**: Handles leader election:
   - Election timers
   - Vote solicitation
   - Leader transitions

4. **HeartbeatManager**: Manages heartbeats:
   - Sending periodic signals (as leader)
   - Monitoring leader activity (as follower)
   - Triggering elections when needed

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

## Configuration Parameters

- **ELECTION_TIMEOUT_MIN/MAX**: Random election timeout range
- **HEARTBEAT_INTERVAL**: Time between heartbeats
- **MAX_MISSED_HEARTBEATS**: Threshold for marking nodes as down