*For replica README, go to replication/README.md*

Design problem 4

other engineering notebook: milestones
https://github.com/mirabor/cs262-chat/issues?q=is%3Aissue%20state%3Aopen%20milestone%3A%22Milestone%203%3A%20Make%20Chat%20Server%202-Fault%20Tolerant%22

3/10/25:

Option 1: primary backup; more practical approach
Option 2: state machine controlling replicas

1. degree of replication: how many backup servers waiting
2. blocking time: worst case scenario for how long a request might be stuck waiting to process
3. failover time: how long a new server to become primary server after failure

client communicates w/ server, server needs to communicate with backups somehow
distributed system: should seem as iif it’s working on one machine

api.py codebase should seem like it’s a single machine
that’s where load balancer/dfifferent layer that handles communication stuff comes in

primary backup: less overhead b/c not persisting updates to the database for every machine
but trickier to reduce failover time because if 2 backups fail, the un-backed up version won’t be able to handle a huge volume of requests from the main?

what is the difference between primary backup and state machine backup?
if you have n machines, how does the primary backup work? 
Let’s say you want a system to be 2-fault tolerant. what happens if the 2 backups fail? How do you ensure there isn’t too much failover time (to update the fourth server and sync it with main)?
Do the backups actually process the requests and update their databases?

3/15/25:

primary backup with main server + 3 additional servers
two additional servers serve as the backups for the main server
third additional server handles updates in the background = eventual consistency

in the case of 2 faults: then the primary backup still handles updates, and it’ll update the third additional server as it fetches updates from the client
the main server doesn’t block, it gets updates from the client even as it updates the third server in the background

n (replication factor): The total number of replicas across which data is stored
w (write quorum): the number of nodes that must acknowledge a write for it to be considered successful
r (read quorum): The number of nodes that must respond with the most recent data version during a read operation

strong consistency: w+r>n

eventual consistency: if w + r ≤ n, allow stale reads

how does the client communicate w/ the server? we have multiple servers, we have many clients that we cna’t count? how do we set it up so there’s no single point of failure

load balancer? would need multiple load balancers
how does client know who the primary server is?

asynch replication > synch replication
eventual consistency > strong consistency for efficiency
tradeoff: even tho it’s faster, stale data during failover, whereas strong consistency keeps backups always current

maintain our existing chat app impl: the difference is where it stores the data
when you start a server, tell it the name of its database so it creates its own replica of the database
but then we run it as it was
therefore we need something on top of server so we know how many servers we have

options: multiple load balancers?
leader election in case of the main one crashes

client has list of IP addresses, connects to server requesting to know the IP address of the leader

maintain the database as it is where the api endpoints query the database
let server be something you call on the api endpoints

fault tolerance can be another layer on its own (load balancer, or something else)) = program that knows one server and can start up replicas of it and can do eventual consistency, all that logic will go in the fault tolerance layer

currently the server has the database, so ideally we would have something that controls the database replicas separately from the server (**stretch goal)

we need an application that can control instances of servers and make sure they’re following some consistency rules

to start, we can say server has the database

the problem is what if the fault tolerance program fails? that’s why you would need multiple load balancers?

but if you don’t use a load balancer, you need logic to make sure leader election is contained in the server code. this is not good because that’s not how it works in production

idea: GCP, client can be hosted anywhere, and then there’s an API gateaway which does the redundancy stuff. maybe we can use an API gateaway? 

we don’t want all the fault tolerance on the backend

something in between client and server handles consistency

so leader election happens in the fault tolerance system

tradeoff: it’s possible to implement leader election by uddating it in our existing server code, which would save us from implementing the fault tolerance layer which needs to be replicated
so yes, we need to replicate the fault tolerance system, but it’s independent of the server and it’s easy to repurpose for a different situation

best practice: implementing a new layer for fault tolerance
that way backend doesn’t have to worry about distribution

when the client talks to the server, it makes an API request to register the user and password. the fault tolerance system knows how many servers there are, has all the configs of n/w/r, it knows which one is the primary. it knows we need to write to 2 and read 1 (for example), but let’s say there are 3 other servers it didn’t make a call to? so then the fault tolerance layer receives an API call from client, ensures the primary and 2 backups are done doing that, and then it gets back to the client, and in the background it updates the other servers so they’re eventually consistent

tradeoff: doesn’t guarantee consistency

**having a new system allows us to have independent failures
let’s say the NWR formula were contained in one server that’s doing a background job; if it goes down then the background jobs will never happen. but if you have the fault tolerance layer and the server goes down, then it’ll be the one leading the other servers.

we ensure that the fault tolerance layer are 2-fault tolerant by including 2 backup fault tolerance layers
the thing handling the backups has 2 backups?

in the case of the fault tolerance layer failing: then the client just moves on to the next layer, it has a reference to the other backups

do all the clients talk to the same load balancer?


3/16/25: How about the lamport’s logical clocks? Can it be a great helper to this? 

Idea: can we reuse the logical clock model we built for demo II as our replication layer? Like it already has logging mechanism and ordering of events over time. So in this case:
-  the virtual machines would be our gRPC server replicas. 
- The process tick can simulate heartbeat replicas checkins
- “Internal” messages types would fall into: 
    * AppendEntries from leader to followers,
    * Acks from followers to leader,
    * Heartbeat messages (which are basically empty AppendEntries),
    * RequestVote and Vote messages (for leader election)


3/17/25: (1) raw sockets vs. (2) gRPC for replication? 

After revisiting both (1) raw sockets and (2) gRPC implementations, it seems like (1) would give us more flexibility to add a replication layer because: 

1. Approach 1: embedding replication layer into server code. If we go with this approach and gRPC, each API endpoint handler function would need to have some logic to communicate w/ other replicas (for leader or just send an ‘acknowledgment’ to the leader). Other option to avoid this manual process would require to touch the gRPC auto-generated code (which isn’t recommended or best practices either). However with socket impl, we have control to all handler in the `server.py` where routing of api calls happen. 
2. Approach 2: having a replication layer on top of server code. For this + gRPC, this would kinda defeat the best part of gRPC (which is client call gRPC stubs as if they are local function, and gRPC handles the middle communication parts). So we’d end up with more code duplications or having to refactor much in the current client code to avoid such duplications. However, with raw sockets, we can have the replication layer get the json payloads from client as and then ensure that operation is replicated as necessary. Which is a bit more straightforward.

So in both cases, seems like raw sockets offers more flexibility for replication. (At least for our current understanding now, we will keep thinking…) 

3/18/25: Let’s decide at this point
(midnight)

Note Entry (Follow-up): After more thinking…
1. Write Operations Only. For replication, only writes (e.g., user creation/deletion, sending messages, updating settings) require replication to all replicas. Read operations do not if we go with leader-based approach. (Using N, W, R’s leader-less approach like in Dynamo’s approach might be overkill for the requirements) 
2. No Separate Middle Layer. Placing a stand-alone “replication layer” in front of or on top of our existing server might sound appealing for keeping the old code untouched, but it introduces extra complexity, a potential single point of failure, and possibly duplicate logic. We aren’t updating all endpoints anyway (which was the first misconception  I had lol). We can have a separate “replication layer”  that the server calls. 
3. Raw Sockets vs. gRPC. We’re now leaning towards gRPC since we don’t have to touch most of the endpoints. Also, just for gaining more familiarity with gRPC. I just wish our logical clock model used gRPC lol (but it’s not that much code anyway, so …)

* this where we can add the heartbeat check in messages
* if a follower hasn't received a such a message after a configurable timeout has passed, it should send RequestVote calls.
* If client tries to write to a follower, it should get an error message informing it the address of current leader
* ...

NEXT TODO: Arch Diagram of Replication Layer

3/20/25: Crunch time

- We just need to replicate 3 API calls that do write operations, so we don’t really need a middle layer
- do gRPC bc more applicable to industry
- 5 replicas to be 2 fault tolerant? to make sure things align with the replicas, you can check if 3 align to see what’s correct; majority-based consensus
    - (we can just use 3 replicas if we have a strong consistency state machine; but if we use eventual consistency then we need 5)

For implementing w/ eventual consistency:
* If leader, replicate the operation; if not leader, redirect (for followers to indicate that they're not the leader)
Testing Plan: Ensure that our chat app still works as used to, but replicas logs their stuff; not need to worry about handling crashes/failovers yet. At this point, we should be able to inspect logs by replicas and ensure they are as expected.
* use make server to take in command line arguments (which would be server addresses) for adding a new server
* need to define what addresses go there, so like make server[host_addr] [peer1_addr} .... [peerN_addr]
* so the server will add at host address and connect to the peer addresses

More like from this paper
https://dl.acm.org/doi/10.1145/1466443.1466448

Ensure that:
* Add metadata section to server response to client listing replica addresses so that the client knows when a new server is added and can retry upon failure

state machine:
* Intercept endpoints in ChatService that does writes (e.x. SendChatMessage, Signup, etc.). This operation should be logged by all replicas in their respective log files.
Testing Plan: Ensure that our chat app still works as used to, but replicas logs their stuff; not need to worry about handling crashes/failovers yet. At this point, we should be able to inspect logs by replicas and ensure they are as expected.
* use make server to take in command line arguments (which would be server addresses) for adding a new server
* need to define what addresses go there, so like make server[host_addr] [peer1_addr} .... [peerN_addr]
* so the server will add at host address and connect to the peer addresses

Ensure that, we:
* Add metadata section to server response to client listing replica addresses so that the client knows when a new server is added and can retry upon failure
https://www.cs.cornell.edu/fbs/publications/SMSurvey.pdf


https://excalidraw.com/#room=85a65dc1d4ee6f6e3d39,Y0BBEb4Tp23B7DuyNXVyow

￼


    - we add replicationhandler instead of the replication layer to handle replication separately
    - we implement the leader replica class contianing api.py, grpc_server.py, db_manager.py, replicationhandler

- heartbeat stuff will resemble the VMs from the logical clock implementation
    - can just talk to the leader
    - replace if action <= send_to_first_threshold from logical clock implementation, if leader then send to peers, if follower then it gets back to leader w/ heartbeat message
    - sleeping can be integrated into heartbeat messages
    - replication handler will resemble the VM codebase where the replicas ~ VMs, but the VM codebase uses TCP/IP and we want to use gRPC
    - currently we have chatserver
    - tcp/ip to act as a VM, grpc for server communication since logical clocks use tcp/icp, so each replica should have its own port that tcp is using for internal communication
    - if we did TCP/IP:
        - VM binds to a port; grpc binds to a port to communicate w/ client, there will be a port made by the VM so the replicas can talk to each other via TCP, every server is now using 2 ports
        - this is unnecessary
    - with gRPC:
        - we have one port, and it can implement multiple service


the arrows between replicas are for internal comm btn servers.
This can with whatever protocol:
    - gRPC: Keep things consisent, strongly typed, 
    - TCP/IP (raw socket): 
                    our logical clock model  uses this for comm btn VMs.
                    so might be easier, but might complicate the codebase
                    with so many moving parts, more code, no consistency, etc. 

Replication layer class: 
    - replication layer will look like VMs, reimplement VM (virtual_machine.py from dist_clock_sim) with gRPC
- make version that uses gRPC
- test it to see if it works the same way as TCP/IP
- and use it to integrate it with the repl_chat
- add to grpc_server.py, GRPCserver class should then use replicaservicer 

the arrows between replicas are for internal comm btn servers.
This can with whatever protocol:
    - gRPC: Keep things consisent, strongly typed,
            currently we have ChatServicer (a service to handle business logic w/ client)
               but we can add a new service (new proto. file)  under the same comm channel but 
                for internal comm w/ replicas 
        

Decision: go with gRPC

Replication layer class: 
    - ...

TODO:

1. How to make VMs in logical clock comm via gRPC?
2. How to add a new server in an existing gRPC server
3. Add replicationServicer(more like VMs in logical clocks) to the existing gRPC server

--- Ensure that Chat server still works as used to, but replicas logs their stuff ---

4. Add a way to handle failover/crashes and consensus (leader election)

3/21/25:

Outlined major todos in Github issues

3/22/25:

ensure issues outlines makes sense

one advantage of using TCP/IP/separate port for internal communication between replicas is that we can just add one line for server.py and grpc_server.py 

TCP implementation has an advantage
this would modularize the replication layer class so that it’s just called in one line by server.py 
separating replication/communication to be on its own port would allow us to have both TCP and gRPC both replicating at the same time

client needs to know if a new server is added
first option: client has a list of all addresses and looks thru them, but this is hardcoded bc client has to know all the addresses at the beginning


when we start client, we can tell it one server to connect to
if that server it connects to a leader, good; if it’s a follower, then it’ll tell the server what the leader is
add a metadata section with replica addresses in every server response to the client
when a client sends a request and it fails, it sees what other replicas to try
so in the server code, all we need to do is retry logic and not hardcode all possible addresses in the system

split up issues s.t. 2.1 -> 3.1 -> 5 is the shortest path to MVP

unit tests:
can either manually test to ensure the message store is persistent, or we can set up a client and write a script to login, kill 2 servers, kill the client too, and then check that the messages are the same
We can call send message function from chat app, ask them to read messages, and check if the message is still there, using client code


3/23/25:

make main.py the entry point for server.py

decouple the logic for grpc_server 

try this for 2.0 PR usage:

```bash
# server instance
make run-server MODE=grpc HOST=127.0.0.1 PORT=5555 PEERS=127.0.0.1:5556,127.0.0.1:5557

# Start the second server instance
make run-server MODE=grpc HOST=127.0.0.1 PORT=5556 PEERS=127.0.0.1:5555,127.0.0.1:5557

# Start the third server instance
make run-server MODE=grpc HOST=127.0.0.1 PORT=5557 PEERS=127.0.0.1:5555,127.0.0.1:5556
```

3/24/25:

if the failure was intentional, then ….
if connected to a leader and then the leader detects that it’s about to shut down, then it can tell the others to start leader election and then fail

for client side implementation:

for leader discovery: should it randomly select from the list of known replicas, or go through the list?
go through the list

to make it simpler on the client:
if client sends to a follower, the follower will just redirect to the leader, and then when the leader is done, the follower will get back to the client
this way the client doesn’t have to do the parsing of the follower’s response

running replicas complete, need to integrate client with server

added tests for Initial Impl of Replication Layer and Launching replicas
addressed comments on client-side

trying to integrate client-side (grpc_logic) with grpc_server, replica_node.py, chatservicer and replication_servicer so that when a client sends a request and it fails, it sees what other replicas to try based on metadata sent from the backend server-side

get documentation for an understanding of the replication layer
and then do client server integration

make new PR pass tests
this is for #3.1, handling crashes and leader election

add documentation for the replication layer

make each server start with its own database copy

3/26/25:

make run-server MODE=grpc SERVER_ID=server1 PORT=5555
make run-server MODE=grpc SERVER_ID=server2 PORT=5556 PEERS=10.250.67.240:5555
make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=10.250.67.240:5555, 10.250.67.240:5556

make run-client MODE=grpc CLIENT_ID=mira SERVER_IP=10.250.67.240 PORT=5555

issue 1: each server needs to start with its own database

issue 2: need to communicate between each other so that the message store is persistent, but not across a single point of storage
goal: once one server goes down, the other users are stil able to log in

ChatServicer.Login: returning results: {'success': False, 'error_message': 'Invalid username or password.'}
2025-03-26 11:16:06,140 - src.services.chatservicer - ERROR - Error adding replica metadata: '_Context' object has no attribute 'add_trailing_metadata'
c^C2025-03-26 11:17:19,172 - __main__ - INFO - 

tests for feat/db-per-replica

test 1:
make 3 servers, crash 2, sign up on server3 (single database)
sign up another server as server1
says added new server, same storage
crash server1
sign up server1 again with the same peers
same storage as original
crash server3
server1 breaks, perpetual leader election

test 2:
make 3 servers
sign up on server 1, log in should be fine on server
log out
crash server1
then you can’t log in


for my reference:
run server on sam’s computer

run:
make run-server MODE=grpc SERVER_ID=server2 PORT=5556 PEERS=10.250.63.58:5555 

make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=10.250.63.58:5555, 10-250-67-240:5556

make run-server MODE=grpc SERVER_ID=server3 PORT=5557 PEERS=10.250.10.214:5555, 10-250.10.214:5556

make run-client MODE=grpc CLIENT_ID=mira SERVER_IP=10.250.63.58 PORT=5555

make run-client MODE=grpc CLIENT_ID=mira SERVER_IP=10.250.10.214 PORT=5555


replicastate is created by the replicanode and contains attributes
electionmanager and heartbeatmanager update the state

leader election + heartbeat mechanisms inspired by raft b/c
- clear role distinctions (leader, follower, candidate)
- term-based leadership
- majority-based voting system

raft applications:
- followers become candidates when they timeout
- when a higher term gets discovered, a node becomes a follower
- candidates become leaders when they get the majority vote

also heartbeat system is raft-inspired
- leaders send periodic heartbeats to show authority
- missing heartbeats -> new elections
- randomized election timeouts trigger leader elections:
    - this is to prevent simultaneous elections, split votes
    - when a follower doesn’t get a heartbeat, it starts an election
    - random timeout (3-6 seconds) to avoid election conflicts
    - timer gets reset whenever a node gets a valid heartbeat from leader


test:
crash 1 and crash 2
