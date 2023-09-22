from typing import List, Optional
import hashlib

from bitcoin_rollup_sim.transaction import Transaction
from bitcoin_rollup_sim.utils.common import chunk_list


def get_merkle_root(txs: List[Transaction]):
    assert len(txs) != 0
    txids = [x.txid for x in txs]
    if len(txids) % 2 == 1:
        txids.append(txids[-1])

    # The first call should have more than 1 items or else it will just return
    return create_merkle_root(txids)


def create_merkle_root(items: List[str]) -> str:
    if len(items) == 1:  # means this is the root
        return items[0]
    if len(items) % 2 == 1:  # make even
        items.append(items[-1])

    pairs = chunk_list(items, 2)
    pair_hashes = [
        hashlib.sha256((x+y).encode('utf-8')).hexdigest()
        for x, y in pairs
    ]
    return create_merkle_root(pair_hashes)


def get_nonce_for(inp: str, difficulty: int) -> Optional[int]:
    """
    inp: formatted str. use inp.format(nonce)
    NOTE: unlike in real(bitcion), here the difficulty keeps decreasing.
    We need to find nonce which makes the hash greater than the
    difficulty(unlike smaller in bitcion).
    """
    for x in range(0, 10**6):
        to_hash = inp.format(x)
        sha = hashlib.sha256(to_hash.encode('utf8')).hexdigest()
        shaval = int(sha, 16)
        if shaval < difficulty:
            return x
    return None


def calculate_new_difficulty(blocks: list):
    # TODO: make actual calculation
    return int(blocks[-1].block_header.difficulty_target/1.000002)
