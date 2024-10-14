# Protocol

2024-10-14

Serial Communication (UART) over USB

## Communication

The Lenlab software is on the USB host and leads the communication.
The Lenlab firmware is on the USB device. It waits for a command and returns a reply.

## Packet format

Packet:

- 1 byte label
- 2 bytes length (little endian)
- length bytes payload
- 4 bytes args (BSL checksum)
- Size: length + 7 bytes

BSL-Ack-Packet:

- 1 byte ack (success 0x00 or error code)
- Size: 1 byte

Compatible packet format between the Lenlab firmware and the Boostrap Loader. The same
host software can handle both device firmwares.

The BSL waits for commands from the host. It replies to each command with an ack packet and to some commands
additionally with a response packet (if the ack was 0x00 ok).

The software distinguishes between Lenlab and BSL by the first byte (ack or label):

- 0x00: BSL ack ok packet
- 0x08: BSL response packet (with payload)
- 0x4C "L": Lenlab packet (with payload either way)
- 0x51 - 0x56: BSL error (1 byte packet)
- 0x80: BSL command packet (with payload from host to BSL)

Reply Parser

- If the first byte of the message is 0 or 0x51 to 0x56, it's a single byte ack message
- If the first byte of the packet is 8 (BSL) or 0x4C (Lenlab), it's a packet with payload. 
  3 bytes header plus payload length (in bytes 2 and 3) plus 4 bytes checksum.
- The reply parser cannot know whether it should wait for a response packet after a BSL ack ok packet.
  It depends on the previous command if there is one or not.

The BSL packet header and footer of data packets comprise 7 bytes. Lenlab packets have a minimum size of 8
to avoid problems with alignment and DMA. The packet header is 3 bytes, the minimum payload is 5 bytes.
Lenlab packets have no footer, these 4 bytes are added to the payload. The payload transmitted is 4 bytes larger
than the payload length in the packet header.

## Reply routing

The Lenlab software sends commands and receives replies asynchronously. It can detect the intended recipient
of a reply by the value of the first byte and call the respective handler for BSL or Lenlab.

The handler of replies from the BSL though does need dynamic routing. A BSL ack packet has no address,
it is intended for the handler of the last command. The BSL object saves a pointer to the callback when sending the
command and delivers the next reply to that callback. This implements a state machine with the callback pointer.

## Probing

The Lenlab software looks for a serial port with matching USB vid and pid. If found, it opens the port and sends
the Lenlab welcome message. If the Lenlab firmware replies with the correct version, the program is ready to operate.
Otherwise, Lenlab displays an error message, a hint for solving it (connect Launchpad, flash firmware image)
and a retry button.

The BSL ignores the Lenlab welcome message and still operates for programming. TODO: It does not ignore it and hangs.
If there was no reply to the welcome message, the programmer may start programming, switch the baudrate,
and send the BSL welcome message. After resetting the microcontroller, the programmer resets the communication
and Lenlab probes anew.

If Lenlab did successfully communicate with the firmware, the user may still reset the board in BSL mode and
start programming. Lenlab does not detect the reset, so in this case, the programmer resets the communication first.

## Reset Detection

Lenlab cannot directly detect a microcontroller reset over USB, because it is actually talking to the debug chip,
which forwards the serial port, but no reset signal. The debug port might provide the reset signal,
but that one is the TI debug interface and difficult to use.

Lenlab could detect the reset with a watchdog and regular pings through the communication link.
This is too much programming effort for only little benefit for now.

## Baudrate

BSL initially 9600 baud, command to increase up to 3 Mbaud.

Lenlab 4 Mbaud. Transfer rate (bytes) about 370 KB/s (measurement in comm_experiment) (theory 390 KB/s).

Note: USB 1 Fullspeed 1 MB/s (red_lenlab, old Launchpad).

Maximum memory 32 KB, transfer time about 86 ms.

The ADC can do up to 4 Msps at 12 bits. Transfer in 1.5 bytes results in 5.7 MB/s, much more than the UART can do.
