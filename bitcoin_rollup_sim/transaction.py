from typing import List
from enum import Enum
import hashlib
from dataclasses import dataclass


class ScriptOps(Enum):
    CHECKSIG = "CHECKSIG"
    EQUALVERIFY = "EQUALVERIFY"
    DUP = "DUP"
    HASH160 = "HASH160"


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

    def __str__(self):
        return " ".join([
            self.transaction_id,
            str(self.vout),
            self.script_sig,
            str(self.sequence),
            self.coinbase,
        ])


@dataclass
class VOut:
    value: int  # Satoshis, 8 bytes original, little endian
    script_pub_key: str

    @classmethod
    def get_for_p2pk(cls, address: str, value: int):
        locking_script = " ".join([
            ScriptOps.DUP.name,
            ScriptOps.HASH160.name,
            address,  # TODO: hash?
            ScriptOps.EQUALVERIFY.name,
            ScriptOps.CHECKSIG.name,
        ])
        return cls(
            value=value,
            script_pub_key=locking_script,
        )

    def __str__(self):
        return " ".join([
            str(self.value),
            self.script_pub_key,
        ])


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
        vinstr = ", ".join([str(x) for x in vin])
        voutstr = ", ".join([str(x) for x in vout])
        instance = cls(
            version=version,
            locktime=locktime,
            vin=vin,
            vout=vout,
        )
        selfstr = "<>".join([
            str(instance.version),
            str(instance.locktime),
            vinstr,
            voutstr
        ])
        selfid = hashlib.sha256(selfstr.encode('utf8')).hexdigest()
        instance.txid = selfid
        return instance

    def __str__(self):
        vinstr = ", ".join([str(x) for x in self.vin])
        voutstr = ", ".join([str(x) for x in self.vout])
        return "".join([
            str(self.version),
            str(self.locktime),
            vinstr,
            voutstr,
            self.txid,
        ])
