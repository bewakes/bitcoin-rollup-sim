import time
import random
import json
import socket
from multiprocessing import Process, Manager

from contextlib import asynccontextmanager
from fastapi import FastAPI

from bitcoin_rollup_sim.node import WalletNode, MinerNode, Node
from bitcoin_rollup_sim.block import Block
from bitcoin_rollup_sim.utils.common import recv_from_sock


def setup_network():
    node_types = [
        WalletNode,
        Node,
        MinerNode,
        WalletNode,
    ]
    nodes = []
    with Manager() as manager:
        peers = manager.dict()

        processes = []
        for nodecls in node_types:
            node = nodecls(peers=peers)
            nodes.append(node)
            peers[node.nid] = node.port
            p = Process(target=node.run)
            processes.append(p)
            # time.sleep(random.randrange(1, 5))

        for p in processes:
            p.start()

        return nodes


def get_balance_for(node):
    conn = socket.create_connection(("localhost", node.port))
    msg = "app:8080 app:getbalance"
    ln = len(msg)
    conn.send(f"{ln}{msg}".encode())
    strdata = recv_from_sock(conn)
    return int(strdata)


def ask_info(app):
    node = app.nodes[0]
    conn = socket.create_connection(("localhost", node.port))
    msg = "app:8080 app:getblocks"
    ln = len(msg)
    conn.send(f"{ln}{msg}".encode())
    strdata = recv_from_sock(conn)
    blocks = [Block.deserialize(x) for x in json.loads(strdata)]
    return {
        "blocks": [x.to_json() for x in blocks],
        "peers": [
            {
                "id": x.nid,
                "pubkey": x.keysaddress.pub_key_hex if hasattr(x, "keysaddress") else "",
                "pubkey_hash": getattr(x, 'pubkeyhash', ''),
                "balance": get_balance_for(x),
            }
            for x in app.nodes
        ],
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.nodes = setup_network()
    yield
    # Clean up the ML models and release the resources

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def get_info():
    data = ask_info(app)
    blocks = data["blocks"]
    return {
        "block_height": len(blocks),
        "peers": data["peers"],
    }


@app.get("/blocks")
async def get_blocks():
    data = ask_info(app)
    blocks = data["blocks"]
    return {
        "block_height": len(blocks),
        "blocks": blocks,
    }
