from io import BytesIO

import pytest

from lenlab.bsl import pack, unpack, ChecksumError


def test_connection():
    assert pack(bytearray([0x12])) == bytes.fromhex("80 01 00 12 3A 61 44 DE")


def test_get_device_info():
    assert pack(bytearray([0x19])) == bytes.fromhex("80 01 00 19 B2 B8 96 49")


def test_device_info():
    payload = bytes.fromhex(
        "31 00 01 00 01 00 00 00 00 01 00 C0 06 60 01 00 20 01 00 00 00 01 00 00 00"
    )
    packet = (
        bytes.fromhex("08 19 00") + payload + bytes.fromhex("49 61 57 8C")
    )
    assert unpack(BytesIO(packet)) == payload


def test_unlock():
    password = bytearray([0xFF]) * 32
    expected = (
        bytes.fromhex("80 21 00 21") + password + bytes.fromhex("02 AA F0 3D")
    )
    assert pack(bytearray([0x21]) + password) == expected


def test_unlocked():
    expected = bytes.fromhex("3B 00")
    assert unpack(BytesIO(bytes.fromhex("08 02 00 3B 00 38 02 94 82"))) == expected


def test_program():
    address = bytes.fromhex("00 00 00 00")
    program = bytes.fromhex("00 00 00 04 00 00 00 08")
    expected = (
        bytes.fromhex("80 0D 00 20") + address + program + bytes.fromhex("7A DC AE B8")
    )
    assert pack(bytearray([0x20]) + address + program) == expected


def test_checksum_error():
    with pytest.raises(ChecksumError):
        unpack(BytesIO(bytes.fromhex("08 02 00 3B 00 38 02 94 81")))


def test_message_too_short():
    with pytest.raises(AssertionError):
        unpack(BytesIO(bytes.fromhex("08 02 00 3B 00 38 02 94")))


def test_message_way_too_short():
    with pytest.raises(AssertionError):
        unpack(BytesIO(bytes.fromhex("08 02 00 3B")))
