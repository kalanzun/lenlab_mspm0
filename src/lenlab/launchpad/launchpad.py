from PySide6.QtSerialPort import QSerialPortInfo

KB = 1024

ti_vid = 0x0451
ti_pid = 0xBEF3

port_description = "XDS110 Class Application/User UART"


def find_vid_pid(
    port_infos: list[QSerialPortInfo], vid: int = ti_vid, pid: int = ti_pid
) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


def find_description(
    port_infos: list[QSerialPortInfo], description: str = port_description
) -> list[QSerialPortInfo]:
    return [port_info for port_info in port_infos if port_info.description() == description]


def find_launchpad(port_infos: list[QSerialPortInfo]) -> list[QSerialPortInfo]:
    ti_ports = find_vid_pid(port_infos)
    matches = find_description(ti_ports)
    return matches if matches else ti_ports


# CRC32, ISO 3309
# little endian, reversed polynom
# These settings are compatible with the CRC peripheral on the microcontroller and the BSL
crc_polynom = 0xEDB88320


def crc(values, seed=0xFFFFFFFF, n_bits=8):
    checksum = seed
    for value in values:
        checksum = checksum ^ value
        for _ in range(n_bits):
            mask = -(checksum & 1)
            checksum = (checksum >> 1) ^ (crc_polynom & mask)

        yield checksum


def last(iterator):
    _item = None
    for _item in iterator:
        pass

    return _item
