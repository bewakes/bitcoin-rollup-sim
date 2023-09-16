from typing import List
import hashlib
from fastecdsa import ecdsa, curve, point


def chunk_list(lst: List, size: int):
    chunks = []
    tmp = []
    for i, x in enumerate(lst):
        tmp.append(x)
        if (i+1) % size == 0:
            chunks.append(tmp)
            tmp = []
    if tmp:
        chunks.append(tmp)
    return chunks


def pubkey_compressed_hash160(pubkey_compressed: int):
    sha = hashlib.sha256(pubkey_compressed.to_bytes(33, 'little'))
    ripemd = hashlib.new("ripemd160")
    ripemd.update(sha.digest())
    return ripemd.digest()


def get_signature(msg: str, priv_key: int):
    hashed = hashlib.sha256(msg.encode("utf-8")).digest()
    r, s = ecdsa.sign(hashed, priv_key, curve.secp256k1)
    # NOTE: In real, DER encoding is done, but I simplify here as below
    rhex = f"{r:#X}"[2:]
    shex = f"{s:#X}"[2:]
    return f"{rhex}:{shex}"


def pubkey_compressed_to_point(pubkey_compressed: int):
    pref = pubkey_compressed // (1 << 256)
    X = pubkey_compressed % (1 << 256)
    c = curve.secp256k1
    Ysq = c.evaluate(X)
    order = c.p
    y = pow(Ysq, (order + 1) // 4, order)
    if order - y < y:
        yeven = y
        yodd = order - y
    else:
        yeven = order - y
        yodd = y
    if pref == 0x02:
        Y = yeven
    else:
        Y = yodd
    return point.Point(X, Y, curve.secp256k1)
