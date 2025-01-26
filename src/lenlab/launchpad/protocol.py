def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + length.to_bytes(2, byteorder="little") + argument[1:]


def command(
    argument: bytes, payload0: int = 0, payload1: int = 0, payload2: int = 0, payload3: int = 0
) -> bytes:
    return b"".join(
        [
            pack(argument, 8),
            payload0.to_bytes(2, byteorder="little"),
            payload1.to_bytes(2, byteorder="little"),
            payload2.to_bytes(2, byteorder="little"),
            payload3.to_bytes(2, byteorder="little"),
        ]
    )
