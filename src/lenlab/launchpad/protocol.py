def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + length.to_bytes(2, byteorder="little") + argument[1:]
