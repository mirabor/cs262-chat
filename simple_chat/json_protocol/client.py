import json
import socket
import tkinter as tk

class JsonClient:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send_request(self, request):
        request_json = json.dumps(request).encode()
        self.sock.send(len(request_json).to_bytes(4, 'big') + request_json)
        response_len = int.from_bytes(self.sock.recv(4), 'big')
        return json.loads(self.sock.recv(response_len).decode())

class GUI(tk.Tk):
    def __init__(self, client):
        super().__init__()
        self.client = client
        # TODO: add UI elements