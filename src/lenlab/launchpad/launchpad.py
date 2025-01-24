from .port_info import PortInfo

KB = 1024

ti_vid = 0x0451
lp_pid = 0xBEF3

tiva_pid = 0x00FD


def find_launchpad(port_infos: list[PortInfo]) -> list[PortInfo]:
    # vid, pid
    port_infos = [pi for pi in port_infos if pi.vid == ti_vid and pi.pid == lp_pid]

    # cu*
    if matches := [pi for pi in port_infos if pi.name.startswith("cu")]:
        port_infos = matches

    # sort by number
    port_infos.sort(key=lambda pi: pi.sort_key)

    return port_infos


def find_tiva_launchpad(port_infos: list[PortInfo]) -> list[PortInfo]:
    # vid, pid
    return [pi for pi in port_infos if pi.vid == ti_vid and pi.pid == tiva_pid]


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
