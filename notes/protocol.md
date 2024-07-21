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

## Reply routing

The Lenlab software sends commands and receives replies asynchronously. It can detect the intended recipient
of a reply by the value of the first byte and call the respective handler (BSL or Lenlab).

The handler of replies from the BSL though does need dynamic routing. A BSL ack packet has no address,
it is intended for the handler of the last command. The BSL object saves a pointer to the callback when sending the
command and delivers the next reply to that callback. This implements a state machine with the callback pointer.

## Probing

The Lenlab software looks for a serial port with matching USB vid and pid. If found, it opens the port and sends
the Lenlab welcome message. If the Lenlab firmware replies with the correct version, the program is ready to operate.
Otherwise, the main window displays an error message, a hint for solving it and a retry button.

The BSL ignores the Lenlab welcome message and still operates for programming.
If the is no reply to the welcome message, the software may switch the baudrate and send the BSL welcome message.
Then, BSL replies and the software switches to the programmer tab.

## Baudrate

BSL initially 9600, command to increase up to 3 Mbaud.

Lenlab 9600 works. 2 and 10 Mbaud work only from the debugger. The BSL does ignore a 10 Mbaud welcome message.
