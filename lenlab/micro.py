from dataclasses import dataclass
from io import BytesIO


@dataclass(frozen=True)
class MicroInteger:
    """Encode and decode microcontroller integers in binary little endian format."""

    n_bytes: int

    def pack(self, value: int) -> bytearray:
        return bytearray((value >> (8 * i)) & 0xFF for i in range(self.n_bytes))

    def unpack(self, packet: BytesIO) -> int:
        message = packet.read(self.n_bytes)
        assert len(message) == self.n_bytes, "Message too short"
        return sum(message[i] << (8 * i) for i in range(self.n_bytes))


uint8 = MicroInteger(1)
uint16 = MicroInteger(2)
uint32 = MicroInteger(4)

