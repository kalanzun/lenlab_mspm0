# Deployment

2024-07-10

## Idea

The students install Python and a lenlab python package from PyPI.

The lenlab python packages contains the lenlab app (GUI) and the firmware binary.
The lenlab app can flash the firmware on the Launchpad.

## Drivers

The Launchpad LP-MSPM0G3507 offers standard serial communication (UART) over USB
with the Bootstrap Loader (flashing) or the lenlab firmware.
No custom drivers or TI drivers necessary.

## Dependencies

While installing lenlab, pip will automatically download
and install the dependencies from PyPI.

## Windows Application Signing

The standard Python installer is signed.
Then, pip may install python packages and the python interpreter may run any python code
on the machine without signing, including lenlab.

The students won't see any Windows warnings about unsigned software.
