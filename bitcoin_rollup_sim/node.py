import random
from typing import Literal, TypeAlias, List
from dataclasses import dataclass

from .transaction import Transaction
from .peers import send_transaction
from .validation import validate_transaction
from .utils.node import get_inputs_for

NodeRole: TypeAlias = Literal["miner", "wallet", "fullnode", "spvnode"]


@dataclass
class Node:
    nid: str
    peers: list[str] = []
    propagated_txns: list[str] = []  # propagated txn ids
    txn_pool: list[str] = []  # Pool of unconfirmed txns
    type = "node"

    def __init__(self):
        self.nid = f"{self.type}-{random.randrange(10000)}"

    def propagate_transaction(self, transaction: Transaction):
        from .global_state import get_node

        self.propagated_txns.append(transaction.txid)

        for peer_id in self.peers:
            send_transaction(peer_id, transaction.serialize())

    def receive_transaction(self, txstr: str):
        try:
            txn = Transaction.deserialize(txstr)
        except Exception:
            print(f"{self.nid} - Unparseable txn received. Ignoring.")
            return
        is_valid = validate_transaction(txn)
        if not is_valid:
            print(f"{self.nid} - Invalid txn received. Ignoring.")
            return
        # Add to txn pool if not already
        if txn.txid not in self.txn_pool:
            self.txn_pool.append(txn.txid)
        # propagate valid transaction
        if txn.txid not in self.propagated_txns:
            self.propagate_transaction(txn)


class WalletNode(Node):
    """
    For simplicity wallet node handles just a single address
    """
    priv_key: int
    pub_key: str
    type = "wallet"

    def pay_to(self, amt_sats: int, addr: str):
        inps = get_inputs_for(self.pub_key, amt_sats)
        # Create txn
        # Add txn pool
        # Propagate
