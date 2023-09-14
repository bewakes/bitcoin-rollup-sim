from typing import List
import time
import hashlib
import random
from dataclasses import dataclass

from .transaction import Transaction, VIn, VOut
from .utils import get_merkle_root, get_nonce_for
from .keys import KeysAddress


Random = random.Random(55)  # PRNG for creating initial coinbase p2pk address

INITIAL_DIFFICULTY = 20**10
INITIAL_TIMESTAMP = 1694692867


@dataclass
class BlockHeader:
    version: int  # 4 bytes in real
    prev_block_hash: str  # 32 bytes in real
    merkle_root: str  # 32 byetes in real
    timestamp: int  # 4 bytes in real
    difficulty_target: float  # 4 bytes in real
    nonce: int  # 4 bytes in real

    def __str__(self):
        return "".join([
            str(self.version),
            str(self.prev_block_hash),
            str(self.merkle_root),
            str(self.timestamp),
            str(self.difficulty_target),
            str(self.nonce),
        ])


@dataclass
class Block:
    block_header: BlockHeader
    num_transactions: int
    transactions: List[Transaction]
    block_size: int = 0

    def get_hash(self) -> str:
        return ""  # TODO

    @classmethod
    def new(
        cls,
        prev_block_hash: str,
        transactions: List[Transaction],
        version=1,
    ):
        merkle_root = get_merkle_root(transactions)
        difficulty_target = INITIAL_DIFFICULTY  # TODO: calculate new
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
            header_str = "".join([
                str(version),
                prev_block_hash,
                merkle_root,
                str(timestamp),
                str(difficulty_target),
            ])
            nonce = get_nonce_for(header_str)
            if nonce is not None:
                header.nonce = nonce
                break

        block_size = len(str(header)) + sum([len(str(tx)) for tx in transactions])
        return cls(
            block_header=header,
            num_transactions=len(transactions),
            block_size=block_size,
            transactions=transactions,
        )


# Genesis coinbase paid to this address
GenesisKeyAddress = KeysAddress.from_priv_key(Random.randrange(0, 2 << 256))

# Only on transaction
GenesisTransactions = [
    Transaction.new(
        vin=[VIn.get_coinbase_input("Learning bitcion", 1)],
        vout=[VOut.get_for_p2pk(GenesisKeyAddress.address, 50)],
    )
]

# NOTE: this takes time to find nonce, since everything is fixed,
# just hardcode the nonce value(TODO)
print("CREATING genesis block")
GenesisBlock = Block.new(
    prev_block_hash=hashlib.sha256(b"").hexdigest(),
    transactions=GenesisTransactions,
)
print("Genesis block created")
