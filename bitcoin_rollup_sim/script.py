import hashlib
from fastecdsa import ecdsa, curve

from .utils.common import pubkey_compressed_hash160, pubkey_compressed_to_point
from .transaction import VOut
from .consts import OPCODES

import logging

logger = logging.getLogger("script")


class Actions:
    @staticmethod
    def op_equal_action(stack: list, *_) -> list:
        o1 = stack.pop()
        o2 = stack.pop()
        stack.append(o1 == o2)
        return stack

    @staticmethod
    def op_equalverify_action(stack: list, *_) -> list:
        o1 = stack.pop()
        o2 = stack.pop()
        if o1 != o2:
            # The exception will be catched in run_stack function below
            raise Exception("equalverify failed")
        return stack

    @staticmethod
    def op_dup_action(stack: list, *_) -> list:
        stack.append(stack[-1])
        return stack

    @staticmethod
    def op_hash160_action(stack: list, *_) -> list:
        # Assume public key is compressed
        pubkeystr = stack.pop()  # hex str
        pubkey = int(pubkeystr, 16)
        digest = pubkey_compressed_hash160(pubkey)
        stack.append(digest.hex())
        return stack

    @staticmethod
    def sig_verify(stack: list, vout_txn: VOut):
        pubkeystr = stack.pop()
        pubkey = int(pubkeystr, 16)
        Q = pubkey_compressed_to_point(pubkey)
        signature = stack.pop()
        rhex, shex = signature.split(":")
        r, s = int(rhex, 16), int(shex, 16)

        msg = vout_txn.serialize()
        msgdigest = hashlib.sha256(msg.encode("utf-8")).digest()
        return ecdsa.verify((r, s), msgdigest, Q, curve.secp256k1), stack

    @staticmethod
    def op_checksig_action(stack: list, vout_txn: VOut) -> list:
        verified, stack = Actions.sig_verify(stack, vout_txn)
        stack.append(verified)
        return stack

    @staticmethod
    def op_checksigverify_action(stack: list, vout_txn) -> list:
        verified, stack = Actions.sig_verify(stack, vout_txn)
        if not verified:
            raise Exception
        return stack

    @staticmethod
    def op_return_action(stack: list, *_) -> list:
        ...


def run_stack(script: list[str], vout: VOut) -> list:
    stack = []
    for item in script:
        if item not in OPCODES:  # means it is data
            stack.append(item)
        else:
            action_name = item.lower() + "_action"
            try:
                action = getattr(Actions, action_name)
                stack = action(stack, vout)  # Add other context as needed
            except Exception:
                return [False]
    return stack
