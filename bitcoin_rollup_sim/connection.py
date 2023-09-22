from typing import Callable
import random
import socket
import random


# How many bytes to represent the size(stringified int) of the data
DATA_LEN_NUM_BYTES = 5
HOSTNAME = "0.0.0.0"

random.seed(400)


class ConnectionMixin:
    def __init__(self):
        self.socket = socket.socket()
        self.nid = "<unnamed node>"
        self.setup()

    def setup(self):
        while True:
            port = random.randrange(2000, 3000)
            try:
                self.socket.bind((HOSTNAME, port))
                self.port = port
                return port
            except Exception:
                self.logger.error(f"Binding to {port} failed. Trying another.")

    def on_receive_message(self):
        print(*args, **kwargs)

    def run(self, peers):
        self.socket.listen(10)   # 10 connections max
        while True:
            conn, addr = self.socket.accept()
            self.logger.info(f"Received connection from {addr}")
            # Read size of data in bytes
            # first N bytes denote stringified number of bytes
            size = int(conn.recv(DATA_LEN_NUM_BYTES))
            data = conn.recv(size).decode()
            self.logger.info(f"Received {size} bytes of data: {data}")
            resp = self.on_receive_message(data)
            if resp is not None:
                ln = str(len(resp)).zfill(DATA_LEN_NUM_BYTES)
                conn.send(f"{ln}{resp}".encode())

    def send(self, port: int, data: str, peer_id="<na>"):
        addr = ("localhost", port)
        s = socket.create_connection(addr)
        ln = str(len(data)).zfill(DATA_LEN_NUM_BYTES)
        s.send(f"{ln}{data}".encode())
        self.logger.info(f"Sent data to {peer_id}({port})")