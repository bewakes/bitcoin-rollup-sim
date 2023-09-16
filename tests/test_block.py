from bitcoin_rollup_sim.block import get_genesis_block, Block

genesis_block_serialized = """
["[1, \\"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\\", \\"6703f24b5ddb09124c8e3766d464c7cdab50650b0018878b8db3fb6d31cfbfb6\\", 1694692863, 110427941548649020598956093796432407239217743554726184882600387580788736, 350254]", 1, ["[\\"ea559d8b0b3dbb03594614ea6d8fa8b968d75dddca7b7b09371c7fccb82eb273\\", 1, 0, [\\"[\\\\\\"\\\\\\", -1, \\\\\\"\\\\\\", 1, \\\\\\"Learning bitcoin\\\\\\"]\\"], [\\"[50, \\\\\\"OP_DUP OP_HASH160 42146bb6914e3e723742e6f79d56116186f86aab OP_EQUALVERIFY OP_CHECKSIG\\\\\\"]\\"]]"], 0]
"""


def test_genesis_serialize():
    block = get_genesis_block()
    assert block.serialize() == genesis_block_serialized.strip()


def test_genesis_deserialize():
    deserialized_block = Block.deserialize(genesis_block_serialized)
    block = get_genesis_block()
    assert block == deserialized_block
