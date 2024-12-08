import re

from PySide6.QtSerialPort import QSerialPortInfo

KB = 1024

ti_vid = 0x0451
ti_pid = 0xBEF3


def find_vid_pid(
    port_infos: list[QSerialPortInfo], vid: int = ti_vid, pid: int = ti_pid
) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


def find_call_up(port_infos: list[QSerialPortInfo]) -> list[QSerialPortInfo]:
    """find the call-up devices on Mac

    port name on old Macs: /dev/tty.serial
    port name on new Macs (arm64?!):

    - cu.usbmodemMG3500011
    - tty.usbmodemMG3500011
    - tty.usbmodemMG3500014
    - cu.usbmodemMG3500014

    cu: call-up (send data)
    tty: receive data (wait for hardware data carrier detect signal)

    If it has port names that start with "cu.", those are the correct ones
    """
    matches = [port_info for port_info in port_infos if port_info.portName().startswith("cu.")]
    return matches if matches else port_infos


def sort_key(port_info: QSerialPortInfo) -> list:
    return [int(p) for p in re.findall(r"\d+", port_info.portName())]


def find_launchpad(port_infos: list[QSerialPortInfo]) -> list[QSerialPortInfo]:
    ti_ports = find_call_up(find_vid_pid(port_infos))
    ti_ports.sort(key=sort_key)
    return ti_ports
