from PySide6.QtSerialPort import QSerialPortInfo

ti_vid = 0x0451
ti_pid = 0xBEF3

port_description = "XDS110 Class Application/User UART"

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
knock_packet = b"Lk\x00\x00nock"
ok_packet = bytes((0x00, 0x08, 0x02, 0x00, 0x3B, 0x06, 0x0D, 0xA7, 0xF7, 0x6B))

KB = 1024


def find_vid_pid(port_infos: list[QSerialPortInfo], vid: int = ti_vid, pid: int = ti_pid) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


def find_description(port_infos: list[QSerialPortInfo], description: str = port_description) -> list[QSerialPortInfo]:
    return [port_info for port_info in port_infos if port_info.description() == description]


def find_launchpad(port_infos: list[QSerialPortInfo]) -> list[QSerialPortInfo]:
    ti_ports = find_vid_pid(port_infos)
    matches = find_description(ti_ports)
    return matches if matches else ti_ports


# CRC32, ISO 3309
# little endian, reversed polynom
# These settings are compatible with the CRC peripheral on the microcontroller
# and the BSL
crc_polynom = 0xEDB88320


def crc(values, seed=0xFFFFFFFF, n_bits=8):
    checksum = seed
    for value in values:
        checksum = checksum ^ value
        for _ in range(n_bits):
            mask = -(checksum & 1)
            checksum = (checksum >> 1) ^ (crc_polynom & mask)

        yield checksum
