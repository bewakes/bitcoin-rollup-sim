from dataclasses import dataclass
from fastecdsa import curve, keys
import base58
import hashlib

from .utils.common import pubkey_compressed_hash160


@dataclass
class KeysAddress:
    priv_key: int
    pub_key: int
    address: str

    def __str__(self):
        return f"Private Key: {self.priv_key:#X}\nPublic Key: {self.pub_key_hash}"  # noqa

    @classmethod
    def new(cls, compress_key=True):
        priv_key = keys.gen_private_key(curve.secp256k1)
        return cls.from_priv_key(priv_key, compress_key)

    @classmethod
    def from_priv_key(cls, priv_key: int, compress_key=True):
        pub_key_ = keys.get_public_key(priv_key, curve.secp256k1)
        if not compress_key:
            prefix = 0x04 << 256
            with_x = prefix | pub_key_.x
            pub_key = with_x << 256 | pub_key_.y
            addr_sha = hashlib.sha256(pub_key.to_bytes(65, 'little'))
            ripemd = hashlib.new("ripemd160")
            ripemd.update(addr_sha.digest())
            digest = ripemd.digest()
        else:
            order = curve.P256.p
            # TODO: I don't know if the following is the proper
            # way to decide odd or even
            is_even = (order - pub_key_.y) < pub_key_.y
            prefix = (0x02 if is_even else 0x03) << 256
            pub_key = prefix | pub_key_.x
            digest = pubkey_compressed_hash160(pub_key)

        prefixed = bytes([0x00, *digest])  # Add version prefix
        checksum = hashlib.sha256(hashlib.sha256(prefixed).digest()).digest()
        checksum_4bytes = checksum[:4]
        checksumed = [*prefixed, *checksum_4bytes]
        addr = base58.b58encode(bytes(checksumed))
        return cls(priv_key, pub_key, addr.decode("utf-8"))

    @property
    def pub_key_hex(self):
        return hex(self.pub_key)[2:]

    @property
    def pub_key_hash(self):
        return pubkey_compressed_hash160(self.pub_key).hex()
