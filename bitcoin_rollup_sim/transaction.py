from typing import List
import json
import hashlib
from dataclasses import dataclass

from .consts import ScriptOps

REWARD_HALF_BLOCKS = 5


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

    def to_json(self):
        return {
            "txn_id": self.transaction_id,
            "vout": self.vout,
            "script_sig": self.script_sig,
            "sequence": self.sequence,
            "coinbase": self.coinbase,
        }

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
    n: int
    value: int  # Satoshis, 8 bytes original, little endian
    script_pub_key: str

    @classmethod
    def get_for_p2pkh(cls, pkeyhash: str, value: int, ind: int):
        locking_script = " ".join(
            [
                ScriptOps.OP_DUP,
                ScriptOps.OP_HASH160,
                pkeyhash,
                ScriptOps.OP_EQUALVERIFY,
                ScriptOps.OP_CHECKSIG,
            ]
        )
        return cls(
            n=ind,
            value=value,
            script_pub_key=locking_script,
        )

    def serialize(self):
        return json.dumps(
            [
                self.n,
                self.value,
                self.script_pub_key,
            ]
        )

    def to_json(self):
        return {
            "n": self.n,
            "value": self.value,
            "script_pub_key": self.script_pub_key,
        }

    @classmethod
    def deserialize(cls, data: str):
        listed = json.loads(data)
        return cls(
            n=int(listed[0]),
            value=int(listed[1]),
            script_pub_key=listed[2],
        )


@dataclass
class Transaction:
    version: int
    locktime: int
    vin: List[VIn]
    vout: List[VOut]
    txid: str = ""

    @classmethod
    def create_coinbase(cls, dest_pubkeyhash: str, coinbase_message: str, blockheight: int):
        # Block reward halves every 20 blocks
        coinbase_value = (50 * 10**8) / (2 **(blockheight // REWARD_HALF_BLOCKS))  # in satoshis
        return cls.new(
            vin=[VIn.get_coinbase_input(coinbase_message, 1)],
            vout=[VOut.get_for_p2pkh(dest_pubkeyhash, coinbase_value, ind=0)],
        )

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

    def to_json(self):
        return {
            "txid": self.txid,
            "version": self.version,
            "locktime": self.locktime,
            "vins": [x.to_json() for x in self.vin],
            "vouts": [x.to_json() for x in self.vout],
        }

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
