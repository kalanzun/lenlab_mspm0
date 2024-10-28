# Lenlab serial communication protocol

## Baudrate

1 Megabaud

## Discovery

Send a knock packet at 1 MBaud and see, if the firmware replies.

BSL is resilient to the knock packet at 1 MBaud. A BSL connect at 9600 Baud immediately is successful.
Test: `test_bsl.test_resilience_to_false_baudrate`
