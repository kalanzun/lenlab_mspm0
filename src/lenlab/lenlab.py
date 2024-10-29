def pack(argument: bytes) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + b"\x00\x00" + argument[1:]
