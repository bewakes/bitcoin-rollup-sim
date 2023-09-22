import random
import time
import logging
import threading

from .transaction import Transaction, VIn, VOut
from .block import Block, get_genesis_block
from .keys import KeysAddress
from .validation import validate_new_transaction, validate_new_block
from .utils.node import get_inputs_for
from .utils.common import get_signature, pubkey_compressed_hash160
from .connection import ConnectionMixin

MIN_TXNS_PER_BLOCK = 3
MAX_TXNS_PER_BLOCK = 10
MIN_TIME_SINCE_LAST_BLOCK = 30  # Seconds
# Only start candidate block mining if there are no min txns in mempool
# and above time has elapsed


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s: %(levelname)s:%(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


class Node(ConnectionMixin):
    nid: str = "<none>"
    port: int = 0
    peers: dict = dict()
    propagated_txns: list[str] = list()
    propagated_blocks: list[str] = list()
    mem_pool: list[Transaction] = list()
    utxo_set: set[str] = set()
    blocks: list[Block] = list([get_genesis_block()])
    type = "full"

    def __init__(self, peers):
        super().__init__()
        self.nid = f"{self.type}-{random.randrange(10000)}"
        self.logger = logging.getLogger(self.nid)
        self.logger.info(f"Running {self.type} node on port {self.port}")

        self.peers = {k: v for k, v in peers.items()}

    def on_receive_message(self, message: str):
        msg_type, data = message.strip().split(" ", 1)
        self.logger.info(f"Message type {msg_type} received with data {data[:20]}")
        if msg_type == "newblock":
            self.process_new_block(data)
        if msg_type == "newtxn":
            self.process_new_transaction(data)

    def send_get_peers_msg(self):
        ...

    def receive_get_peers_response(self):
        ...

    def propagate_block(self, block: Block):
        if block.hash in self.propagated_blocks:
            return

        for peer_id, peer_port in self.peers.items():
            self.send_block(peer_port, block.serialize(), peer_id)

        with threading.Lock():
            self.propagated_blocks.append(block.hash)

    def propagate_transaction(self, transaction: Transaction):
        if transaction.txid in self.propagated_txns:
            return

        for peer_id, port in self.peers.items():
            self.send_transaction(port, transaction.serialize(), peer_id)
        with threading.Lock():
            self.propagated_txns.append(transaction.txid)

    def process_new_transaction(self, txstr: str):
        try:
            txn = Transaction.deserialize(txstr)
        except Exception:
            self.logger.warning("Unparseable txn received. Ignoring.")
            return
        is_valid = validate_new_transaction(txn)
        if not is_valid:
            self.logger.warning("Invalid txn received. Ignoring.")
            return
        # Add to txn pool if not already
        mempool_ids = [x.txid for x in self.mem_pool]
        if txn.txid not in mempool_ids:
            self.mem_pool.append(txn)

        self.propagate_transaction(txn)

    def process_new_block(self, blockstr: str):
        try:
            block = Block.deserialize(blockstr)
        except Exception:
            self.logger.warning("Unparseable block received. Ignoring.")
            return
        is_valid = validate_new_block(block)
        if not is_valid:
            self.logger.warning("Invalid block received. Ignoring.")
            return
        # Add to blocks if not already
        # TODO: make this better
        hashes = [x.hash for x in self.blocks]
        if block.hash not in hashes:
            self.blocks.append(block)
        self.logger.info(f"{len(self.blocks)=}")
        self.logger.info(f"Block hashes: {', '.join([x.hash for x in self.blocks])}")
        # TODO: check for block forks

        # propagate valid transaction
        if block.hash not in self.propagated_blocks:
            self.propagate_block(block)


class WalletNode(Node):
    """
    For simplicity wallet node handles just a single address
    """
    type = "wallet"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keysaddress = KeysAddress.new()

    def pubkeyhash(self):
        return pubkey_compressed_hash160(
            self.keysaddress.pub_key
        ).hex()

    def create_signature(self, vout: VOut) -> str:
        # TODO: I am not entirely sure what to sign. So I'll just sign
        # the serialized vout indicated by vout_ind
        return get_signature(vout.serialize(), self.keysaddress.priv_key)

    def pay_to(self, pkeyhash: str, amt_sats: int):
        self.logger.info(f"Received payment request {amt_sats} Sats to {pkeyhash}")
        inps = get_inputs_for(self.keysaddress.pub_key_hex, amt_sats)
        if not inps:
            self.logger.error(f"Insufficient Funds({amt_sats} sats)!")
            return False
        surplus = sum([vout.value for _, _, vout in inps]) - amt_sats

        # Create txn
        vins = [
            VIn(
                transaction_id=txid,
                vout=vind,
                coinbase="",
                script_sig=" ".join([
                    self.create_signature(vout),
                    str(self.keysaddress.pub_key_hex),
                ]),
                sequence=1,  # TODO: what to do here?
            )
            for txid, vind, vout in inps
        ]
        vouts = [
            VOut.get_for_p2pkh(pkeyhash, amt_sats),
        ]
        if surplus:  # pay back to yourself
            my_keyhash = self.pubkeyhash()
            vouts.append(VOut.get_for_p2pkh(my_keyhash, surplus))

        txn = Transaction.new(vins, vouts)
        self.logger.info(f"Created a new transaction paying {amt_sats} Satoshis to {pkeyhash}")  # noqa

        # Add to txn pool
        self.mem_pool.append(txn)

        # And then propagate
        self.propagate_transaction(txn)
        return True


class MinerNode(WalletNode):
    type = "miner"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mine(self):
        last_block = self.blocks[-1]
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
        # TODO: add fee utxos to all txns

        # Create a coinbase txn
        coinbase = Transaction.create_coinbase(
            self.keysaddress.pub_key_hash,
            f"Minted by {self.nid}",
        )
        # Create candidate block
        self.logger.info(f"Started mining block. Difficulty:{last_block.block_header.difficulty_target}")
        candidate_block = Block.mine(
            last_block.hash,
            [coinbase, *txns],
            self.blocks,
        )
        self.logger.info("Minted block. Now propagating.")

        self.blocks.append(candidate_block)
        self.propagate_block(candidate_block)

        with threading.Lock():
            # Update mem_pool remove included txns
            self.mem_pool = self.mem_pool[MAX_TXNS_PER_BLOCK:]

    def run(self):
        # Run listener in separate thread
        listener_thread = threading.Thread(None, self.listen)
        listener_thread.start()

        while True:
            self.mine()
            time.sleep(10)
