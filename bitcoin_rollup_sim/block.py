from typing import List
import functools
import json
import time
import hashlib
import random
from dataclasses import dataclass

from .transaction import Transaction, VIn, VOut
from .utils.block import get_merkle_root, get_nonce_for, calculate_new_difficulty
from .utils.common import pubkey_compressed_hash160
from .keys import KeysAddress


Random = random.Random(55)  # PRNG for creating initial coinbase p2pk address

INITIAL_DIFFICULTY = 2**237
INITIAL_TIMESTAMP = 1694692863


@dataclass
class BlockHeader:
    version: int  # 4 bytes in real
    prev_block_hash: str  # 32 bytes in real
    merkle_root: str  # 32 byetes in real
    timestamp: int  # 4 bytes in real
    difficulty_target: float  # 4 bytes in real
    nonce: int  # 4 bytes in real

    def serialize_without_nonce(self):
        """Return formatted string to insert nonce"""
        return json.dumps([
            self.version,
            self.prev_block_hash,
            self.merkle_root,
            self.timestamp,
            self.difficulty_target,
            "{}",
        ])

    def serialize(self):
        return json.dumps([
            self.version,
            self.prev_block_hash,
            self.merkle_root,
            self.timestamp,
            self.difficulty_target,
            self.nonce,
        ])

    def to_json(self):
        return {
            "version": self.version,
            "prev_block_hash": self.prev_block_hash,
            "merkle_root": self.merkle_root,
            "timestamp": self.timestamp,
            "difficulty": self.difficulty_target,
            "nonce": self.nonce,
        }

    @classmethod
    def deserialize(cls, data: str):
        [v, p, m, t, d, n] = json.loads(data)
        return cls(
            version=int(v),
            prev_block_hash=p,
            merkle_root=m,
            timestamp=int(t),
            difficulty_target=int(d),
            nonce=int(n),
        )


@dataclass
class Block:
    block_header: BlockHeader
    num_transactions: int
    transactions: List[Transaction]
    block_size: int = 0

    @functools.cached_property
    def hash(self) -> str:
        return hashlib.sha256(self.serialize().encode("utf-8")).hexdigest()

    def serialize(self):
        return json.dumps([
            self.block_header.serialize(),
            self.num_transactions,
            [x.serialize() for x in self.transactions],
            self.block_size,
        ])

    def to_json(self):
        return {
            "header": self.block_header.to_json(),
            "num_txns": self.num_transactions,
            "txns": [x.to_json() for x in self.transactions],
            "block_size": self.block_size,
        }

    @classmethod
    def deserialize(cls, data: str):
        [bh, nt, t, bs] = json.loads(data)
        return cls(
            block_header=BlockHeader.deserialize(bh),
            num_transactions=nt,
            transactions=[Transaction.deserialize(x) for x in t],
            block_size=bs,
        )

    @classmethod
    def new(
        cls,
        prev_block_hash: str,
        transactions: List[Transaction],
        version=1,
    ):
        merkle_root = get_merkle_root(transactions)
        difficulty_target = INITIAL_DIFFICULTY  # TODO: calculate new
        timestamp = int(time.time())
        header = BlockHeader(
            version=version,
            prev_block_hash=prev_block_hash,
            merkle_root=merkle_root,
            timestamp=timestamp,
            difficulty_target=difficulty_target,
            nonce=0,  # this should be changed
        )

        block = cls(
            block_size=0,
            block_header=header,
            num_transactions=len(transactions),
            transactions=transactions,
        )
        block_size = len(block.serialize()) - 3  # noqa: Subtract 3 because block_size=0 present: [0, ...block after block_size field...]
        block.block_size = block_size
        return block

    @classmethod
    def mine(
        cls,
        prev_block_hash: str,
        transactions: List[Transaction],
        blocks: list,
        version=1,
    ):
        merkle_root = get_merkle_root(transactions)
        difficulty_target = calculate_new_difficulty(blocks)
        while True:
            timestamp = int(time.time())
            header = BlockHeader(
                version=version,
                prev_block_hash=prev_block_hash,
                merkle_root=merkle_root,
                timestamp=timestamp,
                difficulty_target=difficulty_target,
                nonce=0,  # this will be changed below
            )
            header_formatted = header.serialize_without_nonce()
            nonce = get_nonce_for(header_formatted, difficulty_target)
            if nonce is not None:
                header.nonce = nonce
                break

        block = cls(
            block_size=0,
            block_header=header,
            num_transactions=len(transactions),
            transactions=transactions,
        )
        block_size = len(block.serialize()) - 3  # noqa: Subtract 3 because block_size=0 present: [0, ...block after block_size field...]
        block.block_size = block_size
        return block


# Genesis coinbase paid to this address
GenesisKeyAddress = KeysAddress.from_priv_key(Random.randrange(0, 2 << 256))

# Only on transaction
pubkeyhash = pubkey_compressed_hash160(GenesisKeyAddress.pub_key).hex()
GenesisTransactions = [
    Transaction.new(
        vin=[VIn.get_coinbase_input("Learning bitcoin", 1)],
        vout=[VOut.get_for_p2pkh(pubkeyhash, 50, ind=0)],
    )
]


def get_genesis_block() -> Block:
    merkle_root = get_merkle_root(GenesisTransactions)
    header = BlockHeader(
        version=1,
        prev_block_hash=hashlib.sha256(b"").hexdigest(),
        merkle_root=merkle_root,
        timestamp=INITIAL_TIMESTAMP,
        difficulty_target=INITIAL_DIFFICULTY,
        nonce=350254,  # noqa: nonce for genesis header, precalculated for above txns, time and so on
    )
    return Block(
        block_header=header,
        num_transactions=len(GenesisTransactions),
        transactions=GenesisTransactions,
    )
