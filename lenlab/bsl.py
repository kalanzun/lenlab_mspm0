"""MSPM0 Bootstrap Loader (BSL)

The MSPM0 Bootstrap Loader (BSL) provides a method to program and verify the device memory
(Flash and RAM) through a standard serial interface (UART or I2C).

User's Guide https://www.ti.com/lit/ug/slau887/slau887.pdf
"""

from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class BSLInteger:
    """Encode and decode Bootstrap Loader integers in binary little endian format."""

    n_bytes: int

    def pack(self, value: int) -> bytearray:
        return bytearray((value >> (8 * i)) & 0xFF for i in range(self.n_bytes))

    def unpack(self, packet: BytesIO) -> int:
        message = packet.read(self.n_bytes)
        assert len(message) == self.n_bytes, "Message too short."
        return sum(message[i] << (8 * i) for i in range(self.n_bytes))


uint8 = BSLInteger(1)
uint16 = BSLInteger(2)
uint32 = BSLInteger(4)


crc_polynom = 0xEDB88320


def checksum(payload: bytes) -> int:
    """Calculate the Bootstrap Loader checksum."""
    crc = 0xFFFFFFFF
    for byte in payload:
        crc = crc ^ byte
        for _ in range(8):
            mask = -(crc & 1)
            crc = (crc >> 1) ^ (crc_polynom & mask)
    return crc


def pack(payload: bytes) -> bytearray:
    """Pack a packet for the Bootstrap Loader."""
    return bytearray().join(
        [
            uint8.pack(0x80),
            uint16.pack(len(payload)),
            payload,
            uint32.pack(checksum(payload)),
        ]
    )


def get_length(packet: BytesIO) -> int:
    """Get the payload length from a packet header (first four bytes)."""
    ack = uint8.unpack(packet)
    assert ack == 0, "First byte (ack) is not zero."

    header = uint8.unpack(packet)
    assert header == 8, "Second byte (header) is not eight."

    length = uint16.unpack(packet)
    return length


def unpack(packet: BytesIO) -> bytes:
    """Unpack a packet from the Bootstrap Loader and verify the checksum."""
    length = get_length(packet)
    payload = packet.read(length)
    assert len(payload) == length, "Message too short."

    crc = uint32.unpack(packet)
    assert checksum(payload) == crc, "Checksum verification failed."

    return payload
