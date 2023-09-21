"""
Since this is a simlulation app, the global state of the blockchain is maintained here
"""

from typing import Tuple, List

# from .node import Node
from .block import get_genesis_block, Block
from .transaction import VOut


GenesisBlock = get_genesis_block()


class GlobalState:
    __nodes: dict = {}
    __blockchain: list[Block] = [GenesisBlock]
    __utxos: list[Tuple[str, List[VOut]]] = [
        (x.txid, x.vout)
        for x in GenesisBlock.transactions
    ]


GLOBAL_STATE = GlobalState()


def get_node(nid: str):
    return GLOBAL_STATE.__nodes.get(nid)


def get_blockchain():
    return GLOBAL_STATE.__blockchain


def get_utxos():
    return GLOBAL_STATE.__utxos
