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
- set up setup for installation

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

