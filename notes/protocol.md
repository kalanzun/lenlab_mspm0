# Lenlab serial communication protocol

## Baudrate

> 1 Megabaud

At 1 MBaud, the round-trip time to request and receive a 28 KB packet is about 320 ms.
The effective transfer rate of the Lenlab protocol is close to 90 KB/s. 

The serial communication through the debug chip on the Launchpad shows a small rate of data corruption.
Packets may arrive incomplete with corrupted data. There seem to be no corrupt but complete packets.

| baudrate | errors per 100 MB |
|----------|-------------------|
| 4 MBaud  | 120               |
| 1 MBaud  | 1                 |

Test: `test_comm:test_28k` "Error" means an incomplete and corrupt packet.

> The application is required to detect and gracefully handle incomplete and corrupt packets.

## Discovery

The USB interface of the XDS110 debug chip on the Launchpad has two serial ports:

- XDS110 Class Application/User UART
- XDS110 Class Auxiliary Data Port

The port information (QtSerialPortInfo) only differs in the description and only on Windows. The order is random.
MacOS shows four ports per Launchpad without description.

> Discovery opens all ports, sends a command, and selects the port which receives a reply.

Discovery guesses a port and checks it first. If the guess was nothing or wrong, it checks the other ports.
It automatically falls back to probing if guessing was not successful.

> Discovery either looks for the firmware (for Lenlab measurement) or the BSL (for programming), not for both.
 
> The programmer explains the reset procedure to the user and performs the discovery when the user clicks start.

> The programmer assumes a unconnected BSL, fresh out of reset, 10 seconds ticking.

BSL expects the connect command once. Freshly started, it does not react to anything but the connect command.
Connected, it replies to another connect command with an error message, "invalid command".

BSL is resilient to the knock packet at 1 MBaud. A BSL connect at 9600 Baud immediately after is successful.
Test: `test_bsl.test_resilience_to_false_baudrate`

The firmware is resilient to the BSL connect packet at 9600 Baud. A knock at 1 MBaud immediately after is successful.
Test: `test_firmware.test_resilience_to_false_baudrate`

### Intended usage

- New Launchpad (TI out-of-box experience): Lenlab offers explanation and the programmer to flash the firmware.
- Launchpad with old firmware: Lenlab offers an update.
- Launchpad with current firmware: Lenlab offers the measurement functions.
- Launchpad with BSL: Lenlab offers the programmer (discovery did not find the firmware and did not connect to the BSL).
- Two Launchpads: One wins at discovery.

### Counterfactual

- If the firmware supported different baud rates, discovery would take longer to send knock packets at all baud rates. 
  The firmware should fall back to the default baud rate or the user should reset the firmware.
- If the firmware actively sent ping or logger packets, discovery would need clever code to distinguish
  valid packets from invalid data at a different baud rate and then reset the firmware.
- If discovery connected both, firmware and BSL, the programmer would need to handle a connected or not connected BSL,
  when the user followed the reset procedure. This code would have timing issues. The request for reset
  by the user and the assumption of a freshly started BSL reduces code complexity. 

## Test suite

The test suite requires the hardware to do error rate and transfer rate measurement,
as well as testing the firmware implementation.

The test suit has a software Launchpad, which generates transmission errors upon request
to test the resilience of the Lenlab software.

## Simplification

It would be cute to change the baudrate dynamically, it's perfectly fine for Lenlab to work with
one single baud rate setting. A single fixed baud rate reduces the complexity of discovery.
Even if it crashed the BSL, the user would just need to reset the board into BSL mode after discovery.

It would be cute to go to 4 MBaud or higher. It's perfectly fine for Lenlab to go slow with 1 MBaud.
It's fast enough for practical use and the error rate is low.
Lenlab can get away with ignoring very few broken packets. Lenlab handles missing logger points gracefully
or waits for the next oscilloscope trigger.

It would be nice, if Lenlab could sync with the state of the Launchpad (firmware, unconnected BSL, connected BSL)
and detect resets. But this would be complex code, and it would send ping packets regularly to detect a reset.

## Packet format

- ack byte (might be alone)
- code byte
- length two bytes
- payload four + length bytes

Lenlab payload:

- argument four bytes
- content length bytes

BSL payload:

- response length bytes
- checksum four bytes

### Ack

- 0 BSL success
- 0x51 - 0x56 BSL error
- L uppercase Lenlab firmware

### BSL acknowledgement

BSL might send a single ack byte or a complete response packet. A single ack byte may be zero on success
or one of the error codes 0x51 - 0x56 (QRSTUV). A complete response packet begins with ack success (zero)
and code eight.

The BSL documentation specifies for each command whether the reply is a single ack or a complete response packet.

## Receiver logic

Module `Terminal`

> The receiver does not depend on timing.

The single BSL ack byte for success (zero) is also a valid beginning of a complete BSL response packet.
Therefore, the receiver is either in `ack_mode` and expects single ack bytes or not in `ack_mode`
and expects complete packets. Lenlab and BSL packets have the same format and same receiver logic.

> The receiver fails fast.

The receiver does not search for a valid packet in the buffer. Any extra bytes front or back or any invalid prefix
and the receiver emits an error and drops the buffer. 
