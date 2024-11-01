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
