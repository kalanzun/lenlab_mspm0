# Discovery

Which port to connect to?



## Launchpad USB device

Vendor ID `0x0451` Texas Instruments

Product ID `0xbef3` CC1352R1 Launchpad

`XDS110 (03.00.00.32) Embed with CMSIS-DAP`

Serial `MG350001`

The Launchpad USB device has 7 interfaces:

- `InterfaceNumber`: 0, `InterfaceClass`: Communications and CDC Control
- `InterfaceNumber`: 1, `InterfaceClass`: CDC Data
- `InterfaceNumber`: 2, `InterfaceClass`: Vendor Specific Class
- `InterfaceNumber`: 3, `InterfaceClass`: Communications and CDC Control
- `InterfaceNumber`: 4, `InterfaceClass`: CDC Data
- `InterfaceNumber`: 5, `InterfaceClass`: Human Interface Device
- `InterfaceNumber`: 6, `InterfaceClass`: Vendor Specific Class

The Launchpad offers two USB CDC (communications device class) devices (serial ports):

- Interfaces 0 and 1 "XDS110 Class Application/User UART"
- Interfaces 3 and 4 "XDS110 Class Auxiliary Data Port"

Note: The TI driver on Windows provides the serial port descriptions. Without TI driver, both serial ports have the same automatic description.

The serial port on interfaces 0 and 1 "XDS110 Class Application/User UART" connects to the UART pins of the microcontroller. This serial port provides communication with the microcontroller UART.

### Windows

Windows shows 2 serial ports (com ports):

- `COM*`: `Hardware-ID`: `USB\VID_0451&PID_BEF3&MI_00`
- `COM*`: `Hardware-ID`: `USB\VID_0451&PID_BEF3&MI_03`

The hardware ids show the CDC Control interface numbers.

`QSerialPortInfo` carries vendor id and product id, but not the interface number. The description only differs if the TI drivers are installed.

Most of the time the com port numbers are in order of the interfaces, but sometimes not. The com port number may be single digit or two digits (COM9, COM10, ...)

### Mac

The new Macs with M-chip show 4 serial ports:

- **cu**.usbmodemMG350001**1**
- **tty**.usbmodemMG350001**1**
- **cu**.usbmodemMG350001**4**
- **tty**.usbmodemMG350001**4**

"cu" (call up) sends data actively, "tty" receives data and waits for a "data carrier detect signal" from the modem. The Launchpad USB device does not generate that signal. The communication with the Launchpad works only through the call up port.

Note: Opening one variant (cu or tty) blocks the other.

The device names comprise the serial number and the CDC Data interface number.

### Linux

- ttyACM0
- ttyACM1

I assume, the serial port numbers are in order.

Symbolic links:

- `/dev/serial/by-id/usb-Texas_Instruments_XDS110__03.00.00.32__Embed_with_CMSIS-DAP_MG350001-if00`
- `/dev/serial/by-id/usb-Texas_Instruments_XDS110__03.00.00.32__Embed_with_CMSIS-DAP_MG350001-if03`

ModemManager:

ModemManager probes new serial ports when they appear. It opens them and blocks them for 30 seconds.

A `udev` rule on the USB device (not the serial port) can discourage ModemManager.



## Qt Serial Port

`QtSerialPortInfo.availablePorts()` returns all ports in random order. Discovery filters them by vendor id and product id and then picks the result with lower port number.

On Windows, it tries both ports and picks the port that receives a reply (in parallel or one after the other).

Note on sorting: The lower number is not necessarily the first element in alphabetical order (COM10, COM9)



## Process

- Check udev rule on Linux. If not: Offer one-click installation with root password
- `QtSerialPortInfo.availablePorts()`
- Filter for vendor id and product id
- Filter for cu variants (on Mac or if there are cu ports in the list)
- Pick the one with the lower port number (or interface number on Mac)
- Windows: Send welcome packet on both ports and pick the one which receives a reply

This process *should* return the correct port. If not:

- `--port` to override the discovery process
- Error message help text suggests trying the other port with example
- Ask for bug report about the assumption being wrong

Checking the interface id seems too much work for too little improvement.

ModemManager can block the port and open fails or open succeeds and then some packets get through and others don't. Checking for a statistic error seems too much work. Lenlab should fail if the udev rule is not installed.

Checking for ModemManager or waiting 30 seconds seems too much work for too little improvement.



## Probing

Lenlab opens the serial port and sends a communication starter packet. The board replies with the firmware version. Lenlab is either ready to use or asks for a firmware update.

Notes:

- The reply time can be very long (I've seen > 400 ms on Windows)
  - Lenlab should display a busy indicator
  - `--timeout` to increase the timeout if necessary
  - What buffer causes the delay and can it be flushed?
    - The debug chip does buffer for the translation from USB to UART. "The internet" suggests it uses DMA and a FIFO trigger level of 2. Packets shall have an even byte size.
- Mac seems not to like quick re-opening of the port
  - Lenlab should open the port once only.
- Permission Error on Linux
  - The error message suggests to add the user to the group with example and restart the session (log out and log in)
- What about XDS110 USB chip firmware updates?

