from typing import Callable
import random
import socket


# How many bytes to represent the size(stringified int) of the data
DATA_LEN_NUM_BYTES = 5
HOSTNAME = "0.0.0.0"


class Runnable:
    def __init__(self):
        self.socket = socket.socket()
        self.nid = "<unnamed node>"
        self.setup()

    def setup(self):
        while True:
            port = random.randrange(2000, 3000)
            try:
                self.socket.bind((HOSTNAME, port))
                print("Listening on:", port)
                self.port = port
                return port
            except Exception:
                print(f"Binding to {port} failed. Trying another.")

    def log(self, *args, **kwargs):
        raise Exception("Not implemented")

    def on_receive_message(self):
        raise Exception("Not implemented")

    def run(self, peers):
        self.log(f"Running node: {self.nid} on port {self.port}")
        self.socket.listen(10)   # 10 connections max
        while True:
            conn, addr = self.socket.accept()
            self.log(f"Received connection from {addr}")
            # Read size of data in bytes
            # first N bytes denote stringified number of bytes
            size = int(conn.recv(DATA_LEN_NUM_BYTES))
            data = str(conn.recv(size))
            self.log(f"Received {size} bytes of data: {data}")
            resp = self.on_receive_message(data)
            if resp is not None:
                ln = str(len(resp)).zfill(DATA_LEN_NUM_BYTES)
                conn.send(f"{ln}{resp}".encode())

    def send(self, port: int, data: str, peer_id="<na>"):
        addr = ("localhost", port)
        s = socket.create_connection(addr)
        ln = str(len(data)).zfill(DATA_LEN_NUM_BYTES)
        s.send(f"{ln}{data}".encode())
        self.log(f"Sent data to {peer_id}({port})")
