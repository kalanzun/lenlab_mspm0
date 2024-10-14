# Deployment

2024-10-14

## Idea

The students install Python and a lenlab python package from PyPI. `uvx` does both at once.

The lenlab python packages contains the lenlab app (GUI) and the firmware binary.
The lenlab app can flash the firmware on the Launchpad.

## Running

In case of `pip install`, the lenlab package should provide a launch script `lenlab` and a `__main__.py`
for `python -m lenlab`.

In case of `uvx lenlab`, the lenlab package includes a launch script "lenlab". `uvx` requires a launch script
with the same name as the package.

## Drivers

The Launchpad LP-MSPM0G3507 offers standard serial communication (UART) over USB
with the Bootstrap Loader (flashing) or the lenlab firmware.
No custom drivers or TI drivers necessary.

## Dependencies

While installing lenlab, pip or uv will automatically download
and install the dependencies from PyPI.

## Windows Application Signing

The standard Python installer and uv are signed.
Then, pip or uv may install python packages and the python interpreter may run any python code
on the machine without signing, including lenlab.

The students won't see any Windows warnings about unsigned software.
