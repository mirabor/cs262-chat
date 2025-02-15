
ChatApp-262

2-3-2025, evening: set up project structure

2-3-2025, late night:

json_protocol/server.py
- chose threading for concurrency. each client connection gets a separate thread to prevent blocking while allowing the server to handle multiple requests.
- read length of incoming JSON, read data, process, send back response
- using threading.Lock for thread-safety to prevent race conditions when creating accounts
- TODO: extend the _process method for other operations besides creating an account

json_protocol/client.py
- chose tkinter after researching common Python GUIs
- set up json client methods init and send request so that we stick with one request-response cycle at a time
- TODO: build UI (haven't used tkinter before, we'll see)

setup.py
- set up setup for installationer


tests/test_json.py
- started writing some tests for creating an account, more operations to follow

2-7-2025, afternoon:

tkinter — assume that people will have a Mac to use our project (lol)

json protocol: each request from the client is a json obj with an "operation" field for the action and other relevant fields; the server processes this, does the action, and sends back a JSON response with a "status" and "message"

#5 seems like a specification on the frontend side, 5 at a time on frontend instead of all at once using a queue or stack, the server actually has all the messages, but the UI can show limited messages

we think queue/stack for displaying messages gets handled on server side, not client side

put message handler on client side, server side, or in between?
- put messagehandler on client side
- put messagetable on server side

if account is deleted, you don't give them access to message that deleted account again
sender needs to know they sent something, but they should get the info that the account was deleted, but the messages that are unread shouldn't get affected
deleting an account = deleting an account, don't care about the messages

user_id, displays first name and last name

once an account is deleted, we don't give them the option to restore their account because we want to ensure true privacy/real deletion

userconfig - we can save each individual's config in a file, or we can put it in another database. con of file is the way you access it and potentially won't scale for more users. a user decides how many messages they want to see, we can store this in a table. we store user_id and MSG_VIEW_LIMIT

UsersTable: we store user_id, nickname, password

MessagesTable: msg_id, message, status, sender_id, receiver_id, timestamp

AccountManager: Create, Delete, Lookup

Auth: Login, Sign up

Then on client side: 
MessageHandler: Load, send

*in order to differentiate if you know people with two same nicknames, always display the username with it
____

Sequence of User Journey:
Client:
User -> Signup vs. Sign-in

example: if you have 1 user who sends you 10 msgs, and your msg limit is 10, you only see your conversation with that one user

we query the number of messages we want from the table and we group them into conversations on the client side

ask "are you sure?" before deleting an account

question: if you have a message that's not delivered, can you delete that message?
question: can receivers delete a sender's message?

when you open a chat, client gets all messages you had? no, we should do that it loads a preset number of messages and there's a button to get more messages

we should test with madeup data to make sure the frontend client able to navigate, then we can figure out how to fetch that info from the server

if username not registered or password is wrong, take user to error page

sign up: another page if username is already taken

we need to show the number of unread messages
we have read, unread, delivered, sent
we are showing the total number of unread messages; does this include the messages that are sent but not delivered (due to the user's mesage cap)?
design choice: total # of unreads is the unread messages that have been sent

does the server know that the recipient is logged in or not? 
surely it must, because it needs to know whether the recipient is logged in in order to decide whether to store the messages or deliver immediately

store the list of logged in users in a table so that we can check if a person is online? so that we can indicate whether they are logged in or not

deleting messages or a set of messages — selectable in tkinter?
need new page

we also need a page that lists all the users and is iterable to see all of them

using tkinter: issues with installing it via just pip. If python installed via homebrew, we need to install tkinter via `brew install python-tk@3.13` which is kinda platform specification. Maybe we should look into other libraries that makes it easy for cross platform

# TODO:
- search for users
- delete messages/select messages for deletion
- display total number of unread messages, including undelivered (NVM)
- log out of account 
- delete account
- button for adding more messages
- arrow keys or reload for fetching more messages

design decision: number of unread messages will be capped by the number of deliverable messages that the user specifies in settings
bc intuitively, it doesn't make sense to mark an undelivered message as unread
that way client doesn't have to worry about messages that are not received

2-8-2025, morning/afternoon:
dividing up communication + fixing backend stuff
sqlite for persistent store
adding bcrypt for hashing password instead of storing as plain text

code review: splitting up the database management into account manager for cleaner code, more modular
ensuring backend works for signup and login
nvm actually... we don't need to hash password on the database side

2-8-25, evening:
finally debugged pytests for all features
fixed backend functions, code review complete
now to work on making diff parts talking to each other

making ui fixes, fixing crashes when deleting
removing delete button from other pages besides homepage/within chats


need to refactor frontend so they're working with dictionaries of the same type/structure as the backend (database.py), we need the dictionaries to have the same structure and then we can worry about how to transmit them

note: can’t just use backend database bc we need read/write from multiple machines

Questions: what does “server is bound to "0.0.0.0", which means it listens on all network interfaces” mean? 

what if the user intends to delete an entire conversation with a person— should they be able to delete the other person's messages too?

we need to change our UI so that you can’t delete a whole conversation

client is connecting using localhost, there’s a port and address
currently client using localhost, which only works if it’s on the same machine, but instead of localhost, for multiple machines, we should use the ip address of the server machine (which are different)
should we hardcore the ip address on the client side?
alt: have server print ip address and have client paste the ip address

for signup, when the user clicks the signup button, the username/nickname/password needs to be put in a dictionary and then passed to the backend, and then it gets back another dictionary that tells it if it was a success or failure
currently it’s doing the actual writing to a file and saying the file was created
but when we connect them, it’ll be more like once you hit that button, it’s going to talk to the backend by giving it a dictionary and receiving another one
going to call the signup function and call api.py 
flag the parts where you make the modifications:
signup button, login button, delete button, etc.

hash on the client side and use import utils

2-9-25, afternoon:

we need to a) connect frontend to backend
and b) make it so system updates across multiple machines

ways to solve: look at slides code, go to office hours?

goal for tomorrow: we want everything to be done except for custom protocol 
and everything is working except functions we need to change

ISSUE 1: we currently have a protocol working fine, frontend works fine, backend works fine, but they’re all independent so we need to integrate them
in the protocol directory we have client and server, we need to take client to be in the client directory and connect it to the PyQt
client has main.py (with PyQt), on the server side we have api.py with the dbmanager.py, protocol directory has protcol and server and client
what we need to do is take protocol/client.py, server starts connection and clients can join, client sends a message, and server stores it and dumps the file
we need to bring that to the client and server directory (not within protcol directory)
frontend we should be using protocol/client.py stuff to talk to server
but if we just move the client.py and server.py files to the client and server side, they’re not going to just work, we need to make sure they’re communicating, and have the client integrate with main.py 

client side: instead of updating the json logic, main.py should use the functions in client.py to process input and output

same on the server side: server.py needs to talk to api.py, they don’t even need to be talking to the database. that’s why we separate the api.py from dbmanager

maybe we should separate main.py into UI and business logic (how it’s handling deletes, etc.). business logic would be the part that needs to go away, beause we need to replace it with client.py 

on the server side, instead of storing it in a file, we need to use api.py to store it in the database, sends back a response 

once we separate the functionalities from the UI in main.py, then we can replace eit with the functionality of client.py to talk to server

then the server will use api.py to send the requests

business logic should be a 1:1 mapping with api.py (signup, etc.)
then once we have that we can replace it with client.py functionalities and have the server process that

mira: sanity checking frontend and backend separation, then we can split

things i want to test: if a person deletes their chats with someone else, does it delete their entire chat history or just the chats that they sent?

multi-select messages for reactions (actually a feature)

2-10-25, afternoon/evening:

issues: what happens if 2 clients sign in at the same time on different accounts? server should be responsible, not db manager
we can delegate it to api.py

right now dbmanager accepts any password, it should compare passwords with what’s in the database

fix test cases for edge cases:
what if they give you username but not nickname, nickname but not username, missing field, etc

Note: need to document how requesting # of messages works; rn we are saying that when the user specifies a message limit, that is for all the unread messages they might have, not just messages with one person. thus they see the [X] most recent unreads, capped at the limit they send.

combining logic.py and client.py: to clarify, client is only responsible for sending requests and displaying responses? api.py handles business logic and data persistence? 

client.py should replace biz logic of logic.py 

need to integrate delete_messages, delete_chats, save_settings, start_chat, and get_user_message_limit into client.yp
**need to update server.py to handle new actions, and interact with api.py 
also need to extend api.py to include the db operations


- save_settings maps to update_view_limit in api.py 
- get_user_message_limit maps to get_user in api.py 

start_chat, delete_chats, and delete_messages need to be implemented as new functions in api.py

need to do more error handling in logic.py before it sends, because sending is costly, so if you can catch some errors before you ask server to talk to client
(we test for this in unittests)

responsibility of chatapplogic is get data from the user
UI calls logic
logic takes in raw data input
sanitizes it
if it’s good, it sends it to the server
if it’s not good, it raises an error or tells UI something’s not working and UI shows a messagebox
references client functionality
sends code to server
if that is good, it returns true
if it’s bad, it tells UI something went wrong

all the methods will have that structure

2-11-2025, afternoon:

Selectors:

import socket
import selectors
import types
sel = selectors.DefaultSelector ()

Explain why we are or aren’t using them 

need to add to dbmanager a function that checks if a user is in the database or not
NVM already taken care of

need to get rid of previous and next buttons
need to fix search (fnmatch not working?)
showing no users found and no chats, even when they exist
Error receiving message: Invalid JSON: Expecting property name enclosed in double quotes: line 1 column 1025 (char 1024)

use AI to write tests
write tests for client/pages

deciding to use file-based approach instead of sqlite3 database, and then multithread?

guarantee that that works, and then we can replace with the communication

hash fix: need unsalted hash

distributed vs. single

increase buffer for now, but TODO: we need to handle the fact that all the chats that involve the user are sent at once, once you have a lot of chats it’s not going to work

increasing buffer to 2048 for now

YAY I finally integrated sqlite3 database with frontend-backend

i just need to test everything now (will use AI)

got rid of previous and next buttons since scrolling is enabled

new privacy feature: “chat started” when someone clicks on your profile

biggest priority:
implement dynamic unreads (read messages)
deliver immediately
custom protocol not working
make tests
make documentation
test custom protocol

potentially add a refresh button


NVM custom protocol works

so we just need to:
fix the unreads
deliver immediately
make tests
make documentation
add benchmarks for custom protocol to measure how efficient it is


Uh… Jittering is an animated feature!

Whenever UI registers a change, it would have to update client
We made a tradeoff with time and delivering a product that works b/c it’s constantly calling the client which is slightly time inefficient, but allowed us to maintain the codebase, and we think that’s reasonable


CODE REVIEW: 

- 
- Terminal ui, will make ti hard for immediately delivery
    - Tink
- Docs too short (not deep) 
- Multiple machine missing
- Protocol good
- Function: 
    - 

Group 32: 

https://github.com/Fudarakulaszlo/CS2620/tree/main/src

- Does it work? 
    - Function: 
        - Protocol good. 
    - Multi machine 
- Is docs clear
- Are test
- Code clear and clean? 


Group : 

https://github.com/Fudarakulaszlo/CS2620/tree/main/src

- Does it work? 
    - Function: 
        - Protocol good. 
    - Multi machine 
        - Yes
- Is docs clear
    - ??
- Are test
    - 
- Code clear and clean? 


2-12-25:

Moving more engineering documentation to issues on Github

Issues left in order of priority:

Dynamic unreads
- Frontend homepage fix
- Backend tracking unreads/reads
- Dynamic event handling

Fix tests
- Client.py is broken
- Logic.py has poor coverage
- Ui.py has poor coverage
- Protocol stuff will be resolved

Benchmarks
- make it consistent

Make documentation clean
- Make new design diagram
- Explain how we satisfy the specific requirements
- Add GIFs of the UI
- Link to the unit tests and screenshot them

we need to mock the relevant pages used, and cover by asserting that those pages were called with the appropriate parameters. for instance, to test def show_chat_page, we need to mock ChatPage initially and then assert that ChatPage was called with the argument self_id


2-13-25:

Various bug squashes

To deal with the dynamic unreads from homepage and instant chat updates:
We can make the design decision to 

a) polling, with a 2-second delay for the chat page, and then a refresh button for homepage
b) selectors
c) pubsub

2-14-25:

polishing docs and squashing the last few bugs

Added enhancements/future directions to the Issues tab on Github

made GIFs of UI demo showing functionality

Improved test coverage

Cleaned up documentation formatting/added design doc for easy navigaiton

Ready to submit! yayay
