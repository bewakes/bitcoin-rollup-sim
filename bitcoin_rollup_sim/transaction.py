from typing import List
import json
import hashlib
from dataclasses import dataclass

from .consts import ScriptOps
from .utils.common import pubkey_compressed_hash160


@dataclass
class VIn:
    transaction_id: str  # original 32 bytes tx hash
    vout: int  # 4 bytes in real
    script_sig: str
    sequence: int  # 4 bytes in real, Used for locktime or disabled(0xFFFFFFFF)
    coinbase: str = ""

    @classmethod
    def get_coinbase_input(cls, data: str, sequence: int):
        # TODO: what is the sequence?
        return cls(
            transaction_id="",  # all bytes 0 in real
            vout=-1,  # all bytes 1 in real
            coinbase=data,  # in v2 blocks, must begin with block height
            script_sig="",
            sequence=sequence,
        )

    def serialize(self) -> str:
        listed = [
            self.transaction_id,
            self.vout,
            self.script_sig,
            self.sequence,
            self.coinbase,
        ]
        return json.dumps(listed)

    @classmethod
    def deserialize(cls, data: str):
        listed = json.loads(data)
        return cls(
            transaction_id=listed[0],
            vout=int(listed[1]),
            script_sig=listed[2],
            sequence=int(listed[3]),
            coinbase=listed[4],
        )


@dataclass
class VOut:
    value: int  # Satoshis, 8 bytes original, little endian
    script_pub_key: str

    @classmethod
    def get_for_p2pkh(cls, pubkey: int, value: int):
        # Assume compressed pubkey
        locking_script = " ".join(
            [
                ScriptOps.OP_DUP,
                ScriptOps.OP_HASH160,
                pubkey_compressed_hash160(pubkey).hex(),
                ScriptOps.OP_EQUALVERIFY,
                ScriptOps.OP_CHECKSIG,
            ]
        )
        return cls(
            value=value,
            script_pub_key=locking_script,
        )

    def serialize(self):
        return json.dumps(
            [
                self.value,
                self.script_pub_key,
            ]
        )

    @classmethod
    def deserialize(cls, data: str):
        listed = json.loads(data)
        return cls(
            value=int(listed[0]),
            script_pub_key=listed[1],
        )


@dataclass
class Transaction:
    version: int
    locktime: int
    vin: List[VIn]
    vout: List[VOut]
    txid: str = ""

    @classmethod
    def new(cls, vin: List[VIn], vout: List[VOut], version=1, locktime=0):
        # Create hash
        instance = cls(
            version=version,
            locktime=locktime,
            vin=vin,
            vout=vout,
        )
        selfstr = instance.serialize()
        selfid = hashlib.sha256(selfstr.encode("utf8")).hexdigest()
        instance.txid = selfid
        return instance

    def serialize(self):
        return json.dumps(
            [
                self.txid,
                self.version,
                self.locktime,
                [x.serialize() for x in self.vin],
                [x.serialize() for x in self.vout],
            ]
        )

    @classmethod
    def deserialize(cls, data: str):
        [txid, ver, lck, vins, vouts] = json.loads(data)
        return cls(
            txid=txid,
            version=int(ver),
            locktime=int(lck),
            vin=[VIn.deserialize(x) for x in vins],
            vout=[VOut.deserialize(x) for x in vouts],
        )
