from .transaction import Transaction, VIn
from .global_state import get_utxos
from .script import run_stack


def validate_transaction(txn: Transaction):
    utxos_map: dict[str, Transaction] = {x.txid: x for x in get_utxos()}
    utxos = [utxos_map.get(x.transaction_id) for x in txn.vin]
    if not all(utxos):
        return False

    for vin, utx in zip(txn.vin, utxos):
        # Run the script
        if utx is None:
            return False
        if not validate_scripts(vin, utx):
            return False
    return True


def validate_scripts(vin: VIn, utx: Transaction):
    # TODO: use witness
    vout = utx.vout[vin.vout]
    locking_script = vout.script_pub_key.split()
    unlocking_script = vin.script_sig.split()
    # TODO: validate scripts in stack separately
    combined = [*unlocking_script, *locking_script]
    result = run_stack(combined, vout)
    if len(result) != 1:
        return False
    return result[0] == 1
