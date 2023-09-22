from typing import List, Tuple, TypeAlias, Optional

from bitcoin_rollup_sim.transaction import Transaction, VOut
from bitcoin_rollup_sim.global_state import GLOBAL_STATE


def check_can_spend(
    vouts: List[VOut],
    pub_key_hash: str
) -> Tuple[Optional[int], Optional[VOut]]:
    for i, vout in enumerate(vouts):
        [_, _, pubhash, *_] = vout.script_pub_key.split()
        if pubhash == pub_key_hash:
            return i, vout
        vout.script_pub_key
    return None, None


VoutInd: TypeAlias = int
Amt: TypeAlias = int


def get_inputs_for(
    pub_key_hash: str,
    amt_sats: int
) -> List[Tuple[str, VoutInd, VOut]]:
    """
    This scans unspent txns that can be spent by pub_key
    """
    utxos = GLOBAL_STATE.get_utxos()
    sum_amt = 0
    items: List[Tuple[str, VoutInd, VOut]] = []
    for txid, vouts in utxos:
        # Check vout for each
        vout_ind, vout = check_can_spend(vouts, pub_key_hash)
        if vout_ind is not None and vout is not None:
            val = vout.value
            sum_amt += val
            items.append((txid, vout_ind, vout))
            if sum_amt >= amt_sats:
                return items
    # If it reaches here, then the amount cannot be satisfied from pubkey
    # spendable utxos
    return []
