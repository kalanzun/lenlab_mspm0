def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 4
    return b"Ll" + length.to_bytes(2, byteorder="little") + argument


class Protocol:
    knock_packet = pack(b"knoc")
