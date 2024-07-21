# Protocol

2024-07-21

Serial Communication (UART) over USB

## Communication

The Lenlab software is on the USB host and leads the communication.
The Lenlab firmware is on the USB device. It waits for a command and returns a reply.

## Packet format

Packet:

- 1 byte ack
- 1 byte code
- 2 bytes length (little endian)
- length bytes payload
- 4 bytes args (BSL checksum)
- Size: length + 8 bytes

BSL-Ack-Packet:

- 1 byte ack (success 0x00 or error code)
- Size: 1 byte

Compatible packet format between the Lenlab firmware and the Boostrap Loader. The same
host software can handle both device firmwares.

The software distinguishes between Lenlab and BSL by the first byte (packet.ack):

- 0x00: BSL packet
- 0x4C "L": Lenlab
- 0x51 - 0x56: BSL error 
