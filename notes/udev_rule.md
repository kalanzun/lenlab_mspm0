# udev rule

2024-12-06

On Linux, a daemon called ModemManager, part of NetworkManager, will probe any serial port and block it for 30 seconds.
Lenlab receives an error "device or resource busy". When ModemManager gives up, Lenlab can finally open the port.

There is a race condition. If Lenlab manages to open the port quickly enough, it can communicate at first.
But communication will stop. Lenlab can close and re-open the port, maybe communicate, but communication will stop again.
When ModemManager gives up, communication starts to work normally.

`udev` triggers ModemManager for new devices. Another udev rule may mark an usb-device to be ignored by ModemManager:

```
ATTRS{idVendor}=="0451", ATTRS{idProduct}=="bef3", ENV{ID_MM_DEVICE_IGNORE}="1"
```

`/etc/udev/rules.d/50-lenlab.rules`

This is the TI vid and pid for the XDS110 debug probe (the usb-device).
