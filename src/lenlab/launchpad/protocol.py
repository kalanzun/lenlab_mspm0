from importlib import metadata


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


def unpack_fw_version(reply: bytes) -> str | None:
    if reply[0:4] == b"L8\x00\x00":
        return "8." + reply[4:8].strip(b"\x00").decode("ascii", errors="strict")


def get_app_version() -> str:
    # compare without bugfix release (third version number)
    major, minor, *rest = metadata.version("lenlab").split(".")
    return f"{major}.{minor}"


def get_example_version_reply() -> bytes:
    version = get_app_version()
    return b"L8\x00\x00" + version[2:].encode("ascii").ljust(4, b"\x00")
