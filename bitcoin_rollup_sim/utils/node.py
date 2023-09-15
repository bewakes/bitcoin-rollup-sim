from typing import List, Tuple

from bitcoin_rollup_sim.transaction import VIn, Transaction
from bitcoin_rollup_sim.global_state import get_utxos


def check_can_spend(utxo: Transaction, pub_key: str) -> Tuple[bool, int | None]:
    # TODO: complete
    return True, 0


def get_inputs_for(pub_key: str, amt_sats: int) -> List[VIn]:
    """
    This scans unspent txns that can be spent by pub_key
    """
    utxos: list[Transaction] = get_utxos()
    # TODO: get from UTXO set
    sum_amt = 0
    for utxo in utxos:
        # Check vout for each
        can_spend, vout_ind = check_can_spend(utxo, pub_key)
        if can_spend:
            sum_amt += utxo.vout[vout_ind].value
    return []
