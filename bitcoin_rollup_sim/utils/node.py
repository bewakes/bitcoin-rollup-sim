from typing import List, Tuple, Literal, TypeAlias, Union

from bitcoin_rollup_sim.transaction import VIn, Transaction
from bitcoin_rollup_sim.global_state import get_utxos


def check_can_spend(utxo: Transaction, pub_key: int) -> int | None:
    raise Exception("Not implemented")
    return True


VoutInd: TypeAlias = int
Amt: TypeAlias = int


def get_inputs_for(
    pub_key: int,
    amt_sats: int
) -> List[Tuple[Transaction, VoutInd, Amt]]:
    """
    This scans unspent txns that can be spent by pub_key
    """
    utxos = get_utxos()
    sum_amt = 0
    items: List[Tuple[Transaction, VoutInd, Amt]] = []
    for utxo in utxos:
        # Check vout for each
        vout_ind = check_can_spend(utxo, pub_key)
        if vout_ind is not None:
            val = utxo.vout[vout_ind].value
            sum_amt += val
            items.append((utxo, vout_ind, val))
            if sum_amt >= amt_sats:
                return items
    # If it reaches here, then the amount cannot be satisfied from pubkey
    # spendable utxos
    return []
