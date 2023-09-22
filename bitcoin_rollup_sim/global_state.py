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

    def get_utxos(self):
        return self.__utxos

    def get_node(self, nid: str):
        return self.__nodes.get(nid)

    def get_blockchain(self):
        return self.__blockchain


GLOBAL_STATE = GlobalState()
