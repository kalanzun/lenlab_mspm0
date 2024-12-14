from importlib import metadata


def pack(argument: bytes, length: int = 0) -> bytes:
    assert len(argument) == 5
    return b"L" + argument[0:1] + length.to_bytes(2, byteorder="little") + argument[1:]


def unpack_fw_version(reply: bytes) -> str:
    if reply[0:4] == b"L8\x00\x00":
        version = reply[4:8].strip(b"\x00").decode("ascii", errors="ignore")
        if version:
            return "8." + version

    return ""


def get_app_version() -> str:
    # compare without bugfix release (third version number)
    major, minor, *rest = metadata.version("lenlab").split(".")
    return f"{major}.{minor}"
