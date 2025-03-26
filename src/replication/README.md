# Replication Leader Documentation

This document describes the leader election and replication system implemented in the CS262 Chat Application. The system follows a consensus-based approach inspired by the Raft algorithm to ensure data consistency across multiple server instances.

## Overview

The replication system enables the chat application to operate in a distributed environment with multiple server instances, providing:

1. **High Availability**: The system continues to function even if some server instances fail
2. **Fault Tolerance**: Data is replicated across multiple servers to prevent data loss
3. **Consistency**: All server instances maintain a consistent view of the data

## Architecture

The replication system consists of the following key components:

### ReplicaNode

The `ReplicaNode` class serves as the main entry point for the replication system. Each server instance runs a `ReplicaNode` that manages:

- Server state (leader, follower, candidate)
- Communication with other replicas
- Election process
- Data replication

### ReplicaState

The `ReplicaState` class maintains all state-related properties of a replica:

- Server identification (ID, address)
- Current term number
- Current role (leader, follower, candidate)
- Leader information
- Peer tracking
- Voting state

### ElectionManager

The `ElectionManager` handles the leader election process:

- Election timer management
- Vote solicitation
- Leader transition
- Term management

### HeartbeatManager

The `HeartbeatManager` is responsible for:

- Sending periodic heartbeats (if leader)
- Monitoring leader liveness (if follower)
- Detecting failed nodes
- Triggering new elections when needed

## Leader Election Process

The leader election process follows these steps:

1. **Initialization**: All nodes start as followers with a random election timeout.

2. **Election Trigger**: If a follower doesn't receive a heartbeat from the leader before its election timeout expires, it:
   - Increments its term number
   - Transitions to candidate state
   - Votes for itself
   - Requests votes from all peers

3. **Vote Collection**: The candidate collects votes from other servers and:
   - If it receives votes from a majority of servers, it becomes the leader
   - If it discovers a higher term, it reverts to follower state
   - If the election times out without a winner, a new election round begins

4. **Leader Establishment**: When a node becomes the leader, it:
   - Cancels its election timer
   - Updates its role to "leader"
   - Notifies all peers of its leadership
   - Begins sending regular heartbeats to maintain authority

## Leader Responsibilities

Once elected, the leader has several key responsibilities:

### 1. Heartbeat Management

The leader sends regular heartbeats to all followers to:
- Maintain its authority
- Prevent new elections
- Keep track of active followers

```python
# Example heartbeat from leader to followers
request = replication.HeartbeatRequest(
    server_id=self.state.server_id,
    term=self.state.term,
    role="leader",
    timestamp=int(time.time()),
)
```

### 2. Network Membership Management

The leader:
- Maintains the authoritative list of servers in the network
- Processes join requests from new servers
- Detects and handles server failures
- Propagates network membership changes to followers

### 3. Operation Replication

The leader:
- Receives all write operations from clients
- Replicates operations to followers
- Ensures operations are applied in the same order on all servers
- Confirms operation success once a majority of servers have acknowledged it

## Follower Responsibilities

Followers in the replication system:

1. Respond to heartbeats from the leader
2. Forward client requests to the leader
3. Apply operations as directed by the leader
4. Monitor leader liveness and initiate elections when necessary

## Configuration Parameters

The replication system is configured with several key parameters:

- **ELECTION_TIMEOUT_MIN**: Minimum election timeout (in seconds)
- **ELECTION_TIMEOUT_MAX**: Maximum election timeout (in seconds)
- **HEARTBEAT_INTERVAL**: Interval between heartbeats (in seconds)
- **MAX_MISSED_HEARTBEATS**: Number of missed heartbeats before a node is considered down

## Failure Handling

The system handles various failure scenarios:

### Leader Failure

If the leader fails:
1. Followers detect the absence of heartbeats
2. After the election timeout, a follower becomes a candidate
3. A new leader is elected
4. The system continues operation under the new leader

### Follower Failure

If a follower fails:
1. The leader detects missed heartbeat acknowledgments
2. After MAX_MISSED_HEARTBEATS, the leader marks the follower as down
3. The leader continues operation with the remaining followers
4. If the follower recovers, it rejoins the network as a follower

### Network Partitions

In case of network partitions:
1. Nodes in the majority partition elect a leader and continue operation
2. Nodes in minority partitions remain as followers or candidates
3. When the partition heals, nodes with lower terms revert to followers

## Implementation Details

### Leader Election

The leader election is implemented in the `ElectionManager` class:

```python
def start_election(self):
    """Start a leader election."""
    # Increment term and vote for self
    self.state.term += 1
    self.state.role = "candidate"
    self.state.voted_for = self.state.server_id
    self.state.votes_received = {self.state.server_id}
    
    # Request votes from all peers
    for peer_id, peer_address in self.state.peers.items():
        if peer_id not in self.state.down_peers:
            threading.Thread(
                target=self.request_vote, args=(peer_id, peer_address)
            ).start()
    
    # Reset the election timer for next round if needed
    self.reset_election_timer()
```

### Heartbeat Mechanism

The heartbeat mechanism is implemented in the `HeartbeatManager` class:

```python
def _send_heartbeats_as_leader(self, last_heartbeat_time, connection_failure_count):
    """Send heartbeats to all followers if this node is the leader."""
    for peer_id, peer_address in self.state.peers.items():
        try:
            with grpc.insecure_channel(peer_address) as channel:
                stub = replication_grpc.ReplicationServiceStub(channel)
                
                request = replication.HeartbeatRequest(
                    server_id=self.state.server_id,
                    term=self.state.term,
                    role="leader",
                    timestamp=int(time.time()),
                )
                
                response = stub.Heartbeat(request, timeout=1)
                
                # Process response...
        except Exception as e:
            # Handle connection failures...
```