from bitcoin_rollup_sim.block import get_genesis_block, Block

genesis_block_serialized = """
["[1, \\"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\\", \\"7afd1d5cac976ad71a62e333569354a9a84fc7dc24443107175b2021ff36fc3c\\", 1694692863, 110427941548649020598956093796432407239217743554726184882600387580788736, 350254]", 1, ["[\\"069551dab0623fa96bd69f15e3a558d4d53dbf3203f4cbacf008945adb8b3e17\\", 1, 0, [\\"[\\\\\\"\\\\\\", -1, \\\\\\"\\\\\\", 1, \\\\\\"Learning bitcion\\\\\\"]\\"], [\\"[50, \\\\\\"DUP HASH160 1vPuYauiqNa3V8TRbBQqiTBcTa3L EQUALVERIFY CHECKSIG\\\\\\"]\\"]]"], 0]
"""


def test_genesis_serialize():
    block = get_genesis_block()
    assert block.serialize() == genesis_block_serialized.strip()


def test_genesis_deserialize():
    deserialized_block = Block.deserialize(genesis_block_serialized)
    block = get_genesis_block()
    assert block == deserialized_block
