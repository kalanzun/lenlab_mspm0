# Protocol

2024-10-14

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
of a reply by the value of the first byte and call the respective handler for BSL or Lenlab.

The handler of replies from the BSL though does need dynamic routing. A BSL ack packet has no address,
it is intended for the handler of the last command. The BSL object saves a pointer to the callback when sending the
command and delivers the next reply to that callback. This implements a state machine with the callback pointer.

## Probing

The Lenlab software looks for a serial port with matching USB vid and pid. If found, it opens the port and sends
the Lenlab welcome message. If the Lenlab firmware replies with the correct version, the program is ready to operate.
Otherwise, Lenlab displays an error message, a hint for solving it (connect Launchpad, flash firmware image)
and a retry button.

The BSL ignores the Lenlab welcome message and still operates for programming.
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
