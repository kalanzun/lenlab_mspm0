# Lenlab serial communication protocol

## Baudrate

1 Megabaud

At 1 MBaud, the round-trip time to request and receive a 28 KB packet is about 320 ms.
The effective transfer rate of the Lenlab protocol is close to 90 KB/s. 

The serial communication through the debug chip on the launchpad shows a small rate of data corruption.
Packets may arrive incomplete with corrupted data. There seem to be no corrupt but complete packets.

| baudrate | errors per 100 MB |
|----------|-------------------|
| 4 MBaud  | 120               |
| 1 MBaud  | 1                 |

Test: `test_comm:test_28kb` "Error" means an incomplete and corrupt packet.

The application is required to detect and gracefully handle incomplete and corrupt packets.

## Discovery

Send a knock packet at 1 MBaud and see, if the firmware replies.

BSL is resilient to the knock packet at 1 MBaud. A BSL connect at 9600 Baud immediately is successful.
Test: `test_bsl.test_resilience_to_false_baudrate`
