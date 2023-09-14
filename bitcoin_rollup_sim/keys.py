from dataclasses import dataclass

from fastecdsa import curve, keys
import base58
import hashlib


@dataclass
class KeysAddress:
    priv_key: int
    pub_key: int
    address: str

    def __str__(self):
        return f"Private Key: {self.priv_key:#X}\nPublic Key: {self.pub_key:#X}\nAddress: {self.address}"  # noqa

    @classmethod
    def new(cls, compress_key=True):
        priv_key = keys.gen_private_key(curve.secp256k1)
        return cls.from_priv_key(priv_key, compress_key)

    @classmethod
    def from_priv_key(cls, priv_key: int, compress_key=True):
        pub_key_ = keys.get_public_key(priv_key, curve.secp256k1)
        if not compress_key:
            prefix = 0x04 << 512
            with_x = prefix | pub_key_.x << 256
            pub_key = with_x | pub_key_.y
            addr_sha = hashlib.sha256(pub_key.to_bytes(65, 'little'))
        else:
            order = curve.P256.p
            is_even = order - pub_key_.x > pub_key_.x
            prefix = (0x02 if is_even else 0x03) << 256
            pub_key = prefix | pub_key_.x
            addr_sha = hashlib.sha256(pub_key.to_bytes(33, 'little'))

        ripemd = hashlib.new("ripemd160")
        ripemd.update(addr_sha.digest())
        digest = ripemd.digest()
        addr = base58.b58encode(bytes([0x00, *digest]))  # Add version prefix
        return cls(priv_key, pub_key, addr.decode("utf-8"))


if __name__ == '__main__':
    print(KeysAddress.new())
