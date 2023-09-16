from bitcoin_rollup_sim.keys import KeysAddress
from bitcoin_rollup_sim.block import GenesisKeyAddress
from bitcoin_rollup_sim.utils.common import pubkey_compressed_to_point

PRIV_KEY = 0x1E99423A4ED27608A15A2616A2B0E9E52CED330AC530EDCC32C8FFC6A526AEDD


def test_pub_key_uncompressed():
    exp_x = 0xF028892BAD7ED57D2FB57BF33081D5CFCF6F9ED3D3D7F159C2E2FFF579DC341A
    exp_y = 0x07CF33DA18BD734C600B96A72BBC4749D5141C90EC8AC328AE52DDFE2E505BDB

    keyaddr = KeysAddress.from_priv_key(PRIV_KEY, compress_key=False)

    q = 1 << 512
    pubkey = keyaddr.pub_key
    prefix = pubkey // q
    assert prefix == 4, "prefix should be 4"

    xy = pubkey % q
    x = xy // (1 << 256)
    y = xy % (1 << 256)

    assert x == exp_x
    assert y == exp_y


def test_pub_key_compressed():
    expected_pubkey = 0x03F028892BAD7ED57D2FB57BF33081D5CFCF6F9ED3D3D7F159C2E2FFF579DC341A
    keyaddr = KeysAddress.from_priv_key(PRIV_KEY, compress_key=True)
    assert hex(keyaddr.pub_key) == hex(expected_pubkey)


def test_pub_key_compressed_to_point():
    pubkey_compressed = 0x03F028892BAD7ED57D2FB57BF33081D5CFCF6F9ED3D3D7F159C2E2FFF579DC341A
    exp_x = 0xF028892BAD7ED57D2FB57BF33081D5CFCF6F9ED3D3D7F159C2E2FFF579DC341A
    exp_y = 0x07CF33DA18BD734C600B96A72BBC4749D5141C90EC8AC328AE52DDFE2E505BDB
    pt = pubkey_compressed_to_point(pubkey_compressed)
    assert hex(pt.x) == hex(exp_x)
    assert hex(pt.y) == hex(exp_y)
