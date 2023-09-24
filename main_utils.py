from multiprocessing import Process, Manager
import json
import socket

from bitcoin_rollup_sim.utils.common import recv_from_sock
from bitcoin_rollup_sim.node import WalletNode, MinerNode, Node
from bitcoin_rollup_sim.block import Block


def setup_network():
    node_types = [
        WalletNode,
        Node,
        WalletNode,
        MinerNode,
        Node,
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


def pay_from_to(app, fromid, toid, amt):
    frmnode = None
    tonode = None
    for node in app.nodes:
        if node.nid == fromid:
            frmnode = node
        elif node.nid == toid:
            tonode = node
    if frmnode is None or tonode is None:
        return
    topubkey = tonode.pubkeyhash
    conn = socket.create_connection(("localhost", frmnode.port))
    msg = f"app:8080 pay {topubkey} {amt}"
    ln = len(msg)
    conn.send(f"{ln}{msg}".encode())


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


def get_node_details(node: Node):
    return {
        "id": node.nid,
        "balance": get_balance_for(node),
    }
