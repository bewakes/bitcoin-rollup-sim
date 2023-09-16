import random
from dataclasses import dataclass

from .transaction import Transaction, VIn, VOut
from .peers import send_transaction
from .validation import validate_transaction
from .utils.node import get_inputs_for
from .utils.common import get_signature

# NodeRole: TypeAlias = Literal["miner", "wallet", "fullnode", "spvnode"]


@dataclass
class Node:
    nid: str
    peers: list[str] = []
    propagated_txns: list[str] = []  # propagated txn ids
    txn_pool: list[str] = []  # Pool of unconfirmed txns
    type = "node"

    def __init__(self):
        self.nid = f"{self.type}-{random.randrange(10000)}"
        # Connect peers

    def send_get_peers_msg(self):
        ...

    def receive_get_peers_response(self):
        ...

    def propagate_transaction(self, transaction: Transaction):
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
    pub_key: int
    address: str
    type = "wallet"

    def create_signature(self, txn: Transaction, vout_ind: int) -> str:
        # TODO: I am not exacly sure what to sign. So I'll just sign
        # the serialized vout indicated by vout_ind
        vout = txn.vout[vout_ind]
        return get_signature(vout.serialize(), self.priv_key)

    def pay_to(self, amt_sats: int, addr: str):
        inps = get_inputs_for(self.pub_key, amt_sats)
        if not inps:
            print(f"{self.nid} - Insufficient Funds({amt_sats} sats)!")
            return
        surplus = sum([x[2] for x in inps]) - amt_sats

        # Create txn
        vins = [
            VIn(
                transaction_id=inp[0].txid,
                vout=inp[1],
                coinbase="",
                script_sig=" ".join([
                    self.create_signature(inp[0], inp[1]),
                    str(self.pub_key),  # TODO: maybe hash
                ]),
                sequence=1,  # TODO: what to do here?
            )
            for inp in inps
        ]
        vouts = [
            VOut.get_for_p2pk(addr, amt_sats),
        ]
        if surplus:  # pay back to yourself
            vouts.append(VOut.get_for_p2pk(self.pub_key, surplus))

        txn = Transaction.new(vins, vouts)

        # Add to txn pool
        self.txn_pool.append(txn.txid)

        # And then propagate
        self.propagate_transaction(txn)
