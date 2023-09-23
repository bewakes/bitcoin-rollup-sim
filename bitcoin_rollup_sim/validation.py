from typing import List, TypeAlias

from .block import Block
from .transaction import Transaction, VIn, VOut
from .script import run_stack

TxId: TypeAlias = str


def validate_new_transaction(txn: Transaction, utxos: dict[TxId, List[VOut]]):
    # check if input txns are in utxo set
    utx_vouts = [utxos.get(x.transaction_id) for x in txn.vin]
    if not all(utx_vouts):
        return False

    for vin, utx_vouts in zip(txn.vin, utx_vouts):
        # Run the script
        if not utx_vouts:
            return False
        if not validate_scripts(vin, utx_vouts):
            return False
    return True


def validate_new_block(block: Block):
    return True


def validate_scripts(vin: VIn, vouts: List[VOut]):
    # TODO: use witness
    filtered_vouts = [x for x in vouts if x.n == vin.vout]
    if not filtered_vouts:
        return False
    vout = filtered_vouts[0]

    locking_script = vout.script_pub_key.split()
    unlocking_script = vin.script_sig.split()

    # TODO: validate scripts in stack separately
    combined = [*unlocking_script, *locking_script]
    result = run_stack(combined, vout)
    if len(result) != 1:
        return False
    return result[0] == 1
