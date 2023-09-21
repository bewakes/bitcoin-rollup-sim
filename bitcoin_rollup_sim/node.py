import random
import time
import logging
from dataclasses import dataclass

from .transaction import Transaction, VIn, VOut
from .peers import send_transaction, send_block
from .block import Block
from .validation import validate_new_transaction
from .utils.node import get_inputs_for
from .utils.common import get_signature, pubkey_compressed_hash160
from .global_state import get_blockchain


MIN_TXNS_PER_BLOCK = 3
MAX_TXNS_PER_BLOCK = 10
MIN_TIME_SINCE_LAST_BLOCK = 30  # Seconds
# Only start candidate block mining if there are no min txns in mempool
# and above time has elapsed


@dataclass
class Node:
    nid: str
    peers: list[str] = []
    propagated_txns: list[str] = []  # propagated txn ids
    propagated_blocks: list[str] = []  # propagated block hashes
    mem_pool: list[Transaction] = []  # Pool of unconfirmed txns
    utxo_set: set[str] = set()  # Set of UTXOs
    type = "node"

    def __init__(self):
        self.nid = f"{self.type}-{random.randrange(10000)}"
        self.logger = logging.getLogger(self.nid)
        # Connect peers
        self.discover_peers()

    def discover_peers(self):
        pass

    def send_get_peers_msg(self):
        ...

    def receive_get_peers_response(self):
        ...

    def propagate_block(self, block: Block):
        bhash = block.get_hash()
        if bhash in self.propagated_blocks:
            return

        for peer_id in self.peers:
            send_block(peer_id, block.serialize())
        self.propagated_blocks.append(block.get_hash())

    def propagate_transaction(self, transaction: Transaction):
        for peer_id in self.peers:
            send_transaction(peer_id, transaction.serialize())
        self.propagated_txns.append(transaction.txid)

    def receive_transaction(self, txstr: str):
        try:
            txn = Transaction.deserialize(txstr)
        except Exception:
            print(f"{self.nid} - Unparseable txn received. Ignoring.")
            return
        is_valid = validate_new_transaction(txn)
        if not is_valid:
            print(f"{self.nid} - Invalid txn received. Ignoring.")
            return
        # Add to txn pool if not already
        if txn.txid not in self.mem_pool:
            self.mem_pool.append(txn)
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

    def pay_to(self, amt_sats: int, pkeyhash: str):
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
            VOut.get_for_p2pkh(pkeyhash, amt_sats),
        ]
        if surplus:  # pay back to yourself
            my_keyhash = pubkey_compressed_hash160(self.pub_key).hex()
            vouts.append(VOut.get_for_p2pkh(my_keyhash, surplus))

        txn = Transaction.new(vins, vouts)

        # Add to txn pool
        self.mem_pool.append(txn)

        # And then propagate
        self.propagate_transaction(txn)


class MinerNode(Node):
    def mine(self):
        blockchain = get_blockchain()
        last_block = blockchain[-1]
        last_block_header = last_block.block_header
        time_since_last_block = int(time.time()) - last_block_header.timestamp

        # Return if not enough items in mempool and min time before mining
        # has not elapsed
        if (
            len(self.mem_pool) < MIN_TXNS_PER_BLOCK
            and time_since_last_block < MIN_TIME_SINCE_LAST_BLOCK
        ):
            return

        # TODO: sort by fees
        txns = self.mem_pool[:MAX_TXNS_PER_BLOCK]
        # Create candidate block
        self.logger.info("Started mining block")
        candidate_block = Block.mine(
            last_block.get_hash(),
            txns,
        )
        self.logger.info("Mined block. Now propagating")
        self.propagate_block(candidate_block)

        # Update mem_pool remove included txns
        self.mem_pool = self.mem_pool[MAX_TXNS_PER_BLOCK:]
