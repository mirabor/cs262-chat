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