# Lenlab serial communication protocol

## Baudrate

> 1 Megabaud

At 1 MBaud, the round-trip time to request and receive a 28 KB packet is about 320 ms.
The effective transfer rate of the Lenlab protocol is close to 90 KB/s. 

The serial communication through the debug chip on the launchpad shows a small rate of data corruption.
Packets may arrive incomplete with corrupted data. There seem to be no corrupt but complete packets.

| baudrate | errors per 100 MB |
|----------|-------------------|
| 4 MBaud  | 120               |
| 1 MBaud  | 1                 |

Test: `test_comm:test_28k` "Error" means an incomplete and corrupt packet.

The application is required to detect and gracefully handle incomplete and corrupt packets.

## Discovery

> Send a knock packet at 1 MBaud and see, if the firmware replies.
> 
> If not, send a BSL connect packet at 9600 Baud and see, if the BSL replies.
> 
> Repeat on all launchpad ports (in parallel).

BSL is resilient to the knock packet at 1 MBaud. A BSL connect at 9600 Baud immediately after is successful.
Test: `test_bsl.test_resilience_to_false_baudrate`

The firmware is resilient to the BSL connect packet at 9600 Baud. A knock at 1 MBaud immediately after is successful.
Test: `test_firmware.test_resilience_to_false_baudrate`

### Port discovery

The USB interface of the XDS110 debug chip on the launchpad has two serial ports:

- XDS110 Class Application/User UART
- XDS110 Class Auxiliary Data Port

The port information only differs in the description and only on Windows. The order is random.
MacOS shows four ports per launchpad.

Discovery opens both ports, sends commands, and selects the port which receives a reply.

#### Scenarios

- No launchpad connected: No port information found, no discovery.
- New launchpad connected, no firmware: Discovery receives no reply, timeout triggers.
- Launchpad with Lenlab firmware, freshly started: Discovery receives a reply, firmware connected.
- Launchpad with BSL firmware: Discovery receives a reply, BSL connected.
- Two launchpads connected: Discovery stops at the first reply. One launchpad wins the race.

#### Counterfactual

- If the firmware supported different baud rates, discovery would take longer to send knock packets at all baud rates. 
The firmware should fall back to the default baud rate or the user should reset the firmware.
- If the firmware actively sent ping or logger packets, discovery would need clever code to distinguish
valid packets from invalid data at a different baud rate and then reset the firmware.

## Test suite

The test suite requires the hardware to do error rate and transfer rate measurement,
as well as testing the firmware implementation.

The test suit has a software launchpad, which generates transmission errors upon request
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

### BSL acknowledge packet

BSL replies to the connect command with an ack (single byte), if it's the first connect.
Otherwise, it replies with a full ok response (10 bytes).

Because the user might reset the launchpad to BSL mode while Lenlab is running,
Lenlab should always expect both replies to the connect command.
