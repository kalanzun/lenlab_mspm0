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

> Send a knock packet at 1 MBaud and see, if the firmware replies.
> 
> If not, send a BSL connect packet at 9600 Baud and see, if the BSL replies.
> 
> Repeat on all Launchpad ports (in parallel).

BSL is resilient to the knock packet at 1 MBaud. A BSL connect at 9600 Baud immediately after is successful.
Test: `test_bsl.test_resilience_to_false_baudrate`

The firmware is resilient to the BSL connect packet at 9600 Baud. A knock at 1 MBaud immediately after is successful.
Test: `test_firmware.test_resilience_to_false_baudrate`

### Port discovery

The USB interface of the XDS110 debug chip on the Launchpad has two serial ports:

- XDS110 Class Application/User UART
- XDS110 Class Auxiliary Data Port

The port information only differs in the description and only on Windows. The order is random.
MacOS shows four ports per Launchpad without description.

Discovery opens both ports, sends commands, and selects the port which receives a reply.

### Scenarios

- No Launchpad connected: No port information found, no discovery.
- New Launchpad connected, no firmware: Discovery receives no reply, timeout triggers.
- Launchpad with Lenlab firmware: Discovery receives a reply, firmware connected.
- Launchpad with BSL firmware: Discovery receives a reply, BSL connected.
- Two Launchpads connected: Discovery stops at the first reply. One Launchpad wins the race.

### Counterfactual

- If the firmware supported different baud rates, discovery would take longer to send knock packets at all baud rates. 
The firmware should fall back to the default baud rate or the user should reset the firmware.
- If the firmware actively sent ping or logger packets, discovery would need clever code to distinguish
valid packets from invalid data at a different baud rate and then reset the firmware.

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

### Code

- 8 BSL response

## BSL acknowledgement

BSL might send a single ack byte or a complete response packet. A single ack byte may be zero on success
or one of the error codes 0x51 - 0x56 (QRSTUV). A complete response packet begins with ack success (zero)
and code eight.

The BSL documentation specifies for each command whether the reply is a single ack or a complete response packet.

## BSL connect

When freshly started, the only command BSL replies to is `connect`. It replies with the single success byte.

When connected, BSL replies to `connect` with an error message; a complete response packet with the message 6
"invalid command".
