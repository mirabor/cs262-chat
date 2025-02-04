import json
import socket
import threading

class JsonServer:
    def __init__(self, host='localhost', port=5001):
        self.host, self.port = host, port
        self.users = {}
        self.messages = {}
        self.lock = threading.Lock()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            while True:
                conn, _ = s.accept()
                threading.Thread(target=self.handle_client, args=(conn,)).start()

    def handle_client(self, conn):
        try:
            while True:
                data_len = int.from_bytes(conn.recv(4), 'big')
                data = json.loads(conn.recv(data_len).decode())
                response = self._process(data)
                response_json = json.dumps(response).encode()
                conn.send(len(response_json).to_bytes(4, 'big') + response_json)
        finally:
            conn.close()

    def _process(self, data):
        if data['operation'] == 'create_account':
            username, password = data['username'], data['password']
            with self.lock:
                if username in self.users:
                    return {'status': 'error', 'message': 'Username exists'}
                self.users[username] = password
                return {'status': 'success', 'message': 'Account created'}
        # TODO: add otber operations here