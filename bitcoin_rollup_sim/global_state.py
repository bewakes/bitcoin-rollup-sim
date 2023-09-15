"""
Since this is a simlulation app, the global state of the blockchain is maintained here
"""

from .node import Node
from .block import get_genesis_block

GLOBAL_STATE = {
    "nodes": dict(),
    "blockchain": [get_genesis_block()],
    "utxos": [],
}


def get_node(nid: str) -> Node | None:
    return GLOBAL_STATE["nodes"].get(nid)


def get_blockchain():
    return GLOBAL_STATE["blockchain"]


def get_utxos():
    return GLOBAL_STATE["utxos"]
