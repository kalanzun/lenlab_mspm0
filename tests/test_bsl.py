from io import BytesIO

import pytest

from lenlab.bsl import BSLInteger, pack, unpack, ChecksumError


@pytest.fixture
def uint8():
    return BSLInteger(1)


@pytest.fixture
def uint16():
    return BSLInteger(2)


@pytest.fixture
def uint32():
    return BSLInteger(4)


def test_uint8_pack(uint8):
    assert uint8.pack(7) == bytearray([7])


def test_uint8_unpack(uint8):
    assert uint8.unpack(BytesIO(b"\x07")) == 7


def test_uint16_pack(uint16):
    assert uint16.pack(1026) == bytearray([2, 4])


def test_uint16_unpack(uint16):
    assert uint16.unpack(BytesIO(b"\x02\x04")) == 1026


def test_uint32_pack(uint32):
    assert uint32.pack(1026) == bytearray([2, 4, 0, 0])


def test_uint32_unpack(uint32):
    assert uint32.unpack(BytesIO(b"\x02\x04\x00\x01")) == 0x01000402


def test_uint32_too_short(uint32):
    with pytest.raises(AssertionError):
        uint32.unpack(BytesIO(b"\x02\x04"))


def test_connection():
    assert pack(bytearray([0x12])) == bytearray.fromhex("80 01 00 12 3A 61 44 DE")


def test_get_device_info():
    assert pack(bytearray([0x19])) == bytearray.fromhex("80 01 00 19 B2 B8 96 49")


def test_device_info():
    payload = bytearray.fromhex(
        "31 00 01 00 01 00 00 00 00 01 00 C0 06 60 01 00 20 01 00 00 00 01 00 00 00"
    )
    packet = (
        bytearray.fromhex("00 08 19 00") + payload + bytearray.fromhex("49 61 57 8C")
    )
    assert unpack(BytesIO(packet)) == payload


def test_unlock():
    password = bytearray([0xFF]) * 32
    expected = (
        bytearray.fromhex("80 21 00 21") + password + bytearray.fromhex("02 AA F0 3D")
    )
    assert pack(bytearray([0x21]) + password) == expected


def test_unlocked():
    expected = bytes.fromhex("3B 00")
    assert unpack(BytesIO(bytes.fromhex("00 08 02 00 3B 00 38 02 94 82"))) == expected


def test_program():
    address = bytearray.fromhex("00 00 00 00")
    program = bytearray.fromhex("00 00 00 04 00 00 00 08")
    expected = (
        bytes.fromhex("80 0D 00 20") + address + program + bytes.fromhex("7A DC AE B8")
    )
    assert pack(bytearray([0x20]) + address + program) == expected


def test_checksum_error():
    with pytest.raises(ChecksumError):
        unpack(BytesIO(bytes.fromhex("00 08 02 00 3B 00 38 02 94 81")))


def test_message_too_short():
    with pytest.raises(AssertionError):
        unpack(BytesIO(bytes.fromhex("00 08 02 00 3B 00 38 02 94")))


def test_message_way_too_short():
    with pytest.raises(AssertionError):
        unpack(BytesIO(bytes.fromhex("00 08 02 00 3B")))
