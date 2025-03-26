# Replication System

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                Replication System                                                      │
│                                                                                                                        │
│  ┌─────────────────────────────────┐        ┌─────────────────────────────────┐        ┌─────────────────────────────┐│
│  │           Leader Node            │        │          Follower Node 1        │        │         Follower Node 2     ││
│  │                                  │        │                                 │        │                             ││
│  │  ┌───────────────────────────┐  │        │  ┌───────────────────────────┐  │        │  ┌─────────────────────────┐││
│  │  │        ReplicaNode        │  │        │  │        ReplicaNode        │  │        │  │        ReplicaNode      ││
│  │  └────────────┬──────────────┘  │        │  └────────────┬──────────────┘  │        │  └────────────┬────────────┘││
│  │               │ creates          │        │               │ creates          │        │               │ creates      ││
│  │               ▼                  │        │               ▼                  │        │               ▼              ││
│  │  ┌───────────────────────────┐  │        │  ┌───────────────────────────┐  │        │  ┌─────────────────────────┐││
│  │  │       ReplicaState        │  │        │  │       ReplicaState        │  │        │  │       ReplicaState      ││
│  │  │                           │  │        │  │                           │  │        │  │                         ││
│  │  │  • role = "leader"        │  │        │  │  • role = "follower"      │  │        │  │  • role = "follower"   ││
│  │  │  • term = N               │  │        │  │  • term = N               │  │        │  │  • term = N            ││
│  │  │  • server_id              │  │        │  │  • server_id              │  │        │  │  • server_id           ││
│  │  │  • leader_id              │◄─┼────────┼──┼─• leader_id               │◄─┼────────┼──┼─• leader_id            ││
│  │  │  • peers                  │  │        │  │  • peers                  │  │        │  │  • peers               ││
│  │  └─┬─────────────┬───────────┬─┘        │  └─┬─────────────┬───────────┬─┘        │  └─┬─────────────┬─────────┬─┘│
│  │    │             │           │          │    │             │           │          │    │             │         │  ││
│  │    │ references  │ references│ references    │ references  │ references│ references    │ references  │ references references
│  │    │ & updates   │ & updates │ & updates│    │ & updates   │ & updates │ & updates│    │ & updates   │ & updates│ & updates
│  │    ▼             ▼           ▼          │    ▼             ▼           ▼          │    ▼             ▼         ▼  ││
│  │  ┌───────────┐ ┌───────────┐┌──────────┐│  ┌───────────┐ ┌───────────┐┌──────────┐│  ┌───────────┐ ┌───────────┐┌──────────┐
│  │  │ Election  │ │ Heartbeat ││Replication││  │ Election  │ │ Heartbeat ││Replication││  │ Election  │ │ Heartbeat ││Replication│
│  │  │ Manager   │ │ Manager   ││ Manager   ││  │ Manager   │ │ Manager   ││ Manager   ││  │ Manager   │ │ Manager   ││ Manager   │
│  │  └───────────┘ └─────┬─────┘└────┬─────┘│  └───────────┘ └─────┬─────┘└────┬─────┘│  └───────────┘ └─────┬─────┘└────┬─────┘│
│  │                      │          │      │                      │          │      │                      │          │      ││
│  │                      │          │      │                      │          │      │                      │          │      ││
│  │                      │          │      │                      │          │      │                      │          │      ││
│  │                      │ initiates│      │                      │ responds │      │                      │ responds │      ││
│  │                      │ heartbeats      │                      │ to       │      │                      │ to       │      ││
│  │                      ▼          ▼      │                      ▼ heartbeats      │                      ▼ heartbeats      ││
│  │                                        │                                        │                                        ││
│  └────────────────┬────────────────┬─────┘        └────────────────┬─────────────┘        └────────────────┬─────────────┘││
│                   │                │                                │                                       │              ││
│                   │                │                                │                                       │              ││
│                   │                └────────────────────────────────┼───────────────────────────────────────┘              ││
│                   │                                                 │                                                      ││
│                   │                                                 │                                                      ││
│                   │   Heartbeats & Operation Replication           │                                                      ││
│                   └─────────────────────────────────────────────────┘                                                      ││
│                                                                                                                            ││
└────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

### Key Components and Relationships

1. **ReplicaNode**:
   - Creates and owns a ReplicaState instance
   - Creates and initializes managers (Election, Heartbeat, Replication)
   - Establishes cross-references between managers
   - Implements replication logic
   - Each node (leader or follower) has its own ReplicaNode instance

2. **ReplicaState**:
   - Contains all state attributes:
     - server_id: Unique identifier for this node
     - role: "leader", "follower", or "candidate"
     - term: Current term number
     - leader_id: ID of the current leader
     - peers: Map of peer server IDs to addresses
     - election_timer: Timer for triggering elections
     - voted_for: Server ID this node voted for
     - votes_received: Set of servers that voted for this node
   - Created by ReplicaNode
   - Is referenced and updated by all managers

3. **ElectionManager**:
   - References and updates the ReplicaState
   - Manages election timers and timeouts
   - Handles vote solicitation and collection
   - Updates state when becoming leader or candidate
   - Triggers state transitions based on election results

4. **HeartbeatManager**:
   - References and updates the ReplicaState
   - References the ElectionManager to trigger elections
   - In leader: Sends heartbeats to followers
   - In followers: Responds to heartbeats, monitors leader liveness
   - Updates peer status in the state

5. **ReplicationManager**:
   - Present in all nodes (leader and followers)
   - References and updates the ReplicaState
   - In leader: Actively initiates operation replication to followers
   - In followers: Processes replicated operations via ReplicateOperation gRPC service
   - Ensures consensus before committing operations
   - Tracks successful replication across the cluster

### Communication Flow

- **Leader → Followers**: 
  - Heartbeats: Regular messages to signal leader liveness
  - Replication: Operations that need to be applied across the cluster
  
- **Followers → Leader**:
  - Heartbeat responses: Acknowledge leader messages
  - Vote responses: During elections
  
- **State Synchronization**:
  - Leader maintains authoritative state
  - Followers update their state based on leader messages
  - All nodes can trigger elections if leader fails

### Replication Process

1. **Leader Side**:
   - When an operation is received, the leader executes it locally
   - The ReplicationManager sends the operation to all followers
   - The leader waits for a majority of acknowledgments
   - Once consensus is reached, the operation is considered committed

2. **Follower Side**:
   - Followers receive operations via the ReplicateOperation gRPC service
   - The ReplicationManager processes the operation without triggering further replication
   - Followers execute the operation locally and update their state
   - Followers send acknowledgment back to the leader