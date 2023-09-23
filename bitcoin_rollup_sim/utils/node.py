from typing import List, Tuple, TypeAlias, Optional

from bitcoin_rollup_sim.transaction import VOut


def check_can_spend(
    vouts: List[VOut],
    pub_key_hash: str
) -> Optional[VOut]:
    for vout in vouts:
        [_, _, pubhash, *_] = vout.script_pub_key.split()
        if pubhash == pub_key_hash:
            return vout
        vout.script_pub_key
    return None


VoutInd: TypeAlias = int
Amt: TypeAlias = int


def get_inputs_for(
    pub_key_hash: str,
    amt_sats: int,
    utxos: dict[str, list[VOut]],
) -> List[Tuple[str, VOut]]:
    """
    This scans unspent txns that can be spent by pub_key
    """
    sum_amt = 0
    items: List[Tuple[str, VOut]] = []
    for txid, vouts in utxos.items():
        # Check vout for each
        vout = check_can_spend(vouts, pub_key_hash)
        if vout is not None:
            val = vout.value
            sum_amt += val
            items.append((txid, vout))
            if sum_amt >= amt_sats:
                return items
    # If it reaches here, then the amount cannot be satisfied from pubkey
    # spendable utxos
    return []


def get_balance_for(
    pub_key_hash: str,
    utxos: dict[str, list[VOut]],
) -> int:
    """
    This scans unspent txns that can be spent by pub_key
    """
    sum_amt = 0
    for txid, vouts in utxos.items():
        # Check vout for each
        vout = check_can_spend(vouts, pub_key_hash)
        if vout is not None:
            val = vout.value
            sum_amt += val
    return sum_amt
