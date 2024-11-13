KB = 1024

ti_vid = 0x0451
ti_pid = 0xBEF3

port_description = "XDS110 Class Application/User UART"


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
