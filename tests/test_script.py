from bitcoin_rollup_sim.block import GenesisKeyAddress, GenesisTransactions
from bitcoin_rollup_sim.script import run_stack
from bitcoin_rollup_sim.utils.common import get_signature


def test_script_valid_checksig():
    vout = GenesisTransactions[0].vout[0]
    vserialized = vout.serialize()
    locking_script = vout.script_pub_key

    priv_key = GenesisKeyAddress.priv_key
    signature = get_signature(vserialized, priv_key)

    pubkeyhex = hex(GenesisKeyAddress.pub_key)[2:]
    unlocking_script = [signature, pubkeyhex]

    stack = run_stack([*unlocking_script, *locking_script.split()], vout)
    assert stack == [True]


def test_script_invalid_data():
    """
    Test by modifying vout value
    """
    vout = GenesisTransactions[0].vout[0]
    locking_script = vout.script_pub_key

    priv_key = GenesisKeyAddress.priv_key
    # modify vout data
    vserialized = vout.serialize() + "some data"
    signature = get_signature(vserialized, priv_key)

    pubkeyhex = hex(GenesisKeyAddress.pub_key)[2:]
    unlocking_script = [signature, pubkeyhex]

    stack = run_stack([*unlocking_script, *locking_script.split()], vout)
    assert stack == [False]


def test_script_invalid_priv_key():
    """
    Test by modifying signing private key
    """
    vout = GenesisTransactions[0].vout[0]
    locking_script = vout.script_pub_key

    priv_key = GenesisKeyAddress.priv_key + 1  # Making this invalid
    vserialized = vout.serialize()
    signature = get_signature(vserialized, priv_key)

    pubkeyhex = hex(GenesisKeyAddress.pub_key)[2:]
    unlocking_script = [signature, pubkeyhex]

    stack = run_stack([*unlocking_script, *locking_script.split()], vout)
    assert stack == [False]
