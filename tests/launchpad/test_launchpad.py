import pytest

from lenlab.launchpad import launchpad
from lenlab.launchpad.port_info import PortInfo

examples = [
    {
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "linux",
            "kernelVersion": "6.12.1-gentoo-gentoo-dist",
            "prettyProductName": "Gentoo Linux",
            "productType": "gentoo",
            "productVersion": "2.17",
        },
        "available_ports": [
            {
                "description": "XDS110  03.00.00.25  Embed with CMSIS-DAP",
                "manufacturer": "Texas Instruments",
                "portName": "ttyACM0",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/ttyACM0",
            },
            {
                "description": "XDS110  03.00.00.25  Embed with CMSIS-DAP",
                "manufacturer": "Texas Instruments",
                "portName": "ttyACM1",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/ttyACM1",
            },
        ],
        "uart_port": "ttyACM0",
        "ports": ["ttyACM0", "ttyACM1"],
    },
    {
        "sys_info": {
            "currentCpuArchitecture": "arm64",
            "kernelType": "darwin",
            "kernelVersion": "23.6.0",
            "prettyProductName": "macOS Sonoma (14.6)",
            "productType": "macos",
            "productVersion": "14.6",
        },
        "available_ports": [
            {"portName": "cu.Bluetooth-Incoming-Port"},
            {"portName": "tty.Bluetooth-Incoming-Port"},
            {
                "description": "USB ACM",
                "manufacturer": "Texas Instruments",
                "portName": "cu.usbmodemMG3500014",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/cu.usbmodemMG3500014",
            },
            {
                "description": "USB ACM",
                "manufacturer": "Texas Instruments",
                "portName": "tty.usbmodemMG3500014",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/tty.usbmodemMG3500014",
            },
            {
                "description": "USB ACM",
                "manufacturer": "Texas Instruments",
                "portName": "cu.usbmodemMG3500011",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/cu.usbmodemMG3500011",
            },
            {
                "description": "USB ACM",
                "manufacturer": "Texas Instruments",
                "portName": "tty.usbmodemMG3500011",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/tty.usbmodemMG3500011",
            },
        ],
        "uart_port": "cu.usbmodemMG3500011",
        "ports": ["cu.usbmodemMG3500011", "cu.usbmodemMG3500014"],
    },
    {
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "linux",
            "kernelVersion": "6.11.8-300.fc41.x86_64",
            "prettyProductName": "Fedora Linux 41 (Workstation Edition)",
            "productType": "fedora",
            "productVersion": "41",
        },
        "available_ports": [
            {
                "description": "XDS110  03.00.00.32  Embed with CMSIS-DAP",
                "manufacturer": "Texas Instruments",
                "portName": "ttyACM0",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/ttyACM0",
            },
            {
                "description": "XDS110  03.00.00.32  Embed with CMSIS-DAP",
                "manufacturer": "Texas Instruments",
                "portName": "ttyACM1",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "/dev/ttyACM1",
            },
            {"portName": "ttyS0"},
            {"portName": "ttyS1"},
            {"portName": "ttyS10"},
            {"portName": "ttyS11"},
            {"portName": "ttyS12"},
            {"portName": "ttyS13"},
            {"portName": "ttyS14"},
            {"portName": "ttyS15"},
            {"portName": "ttyS16"},
            {"portName": "ttyS17"},
            {"portName": "ttyS18"},
            {"portName": "ttyS19"},
            {"portName": "ttyS2"},
            {"portName": "ttyS20"},
            {"portName": "ttyS21"},
            {"portName": "ttyS22"},
            {"portName": "ttyS23"},
            {"portName": "ttyS24"},
            {"portName": "ttyS25"},
            {"portName": "ttyS26"},
            {"portName": "ttyS27"},
            {"portName": "ttyS28"},
            {"portName": "ttyS29"},
            {"portName": "ttyS3"},
            {"portName": "ttyS30"},
            {"portName": "ttyS31"},
            {"portName": "ttyS4"},
            {"portName": "ttyS5"},
            {"portName": "ttyS6"},
            {"portName": "ttyS7"},
            {"portName": "ttyS8"},
            {"portName": "ttyS9"},
        ],
        "uart_port": "ttyACM0",
        "ports": ["ttyACM0", "ttyACM1"],
    },
    {
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "winnt",
            "kernelVersion": "10.0.22631",
            "prettyProductName": "Windows 11 Version 23H2",
            "productType": "windows",
            "productVersion": "11",
        },
        "available_ports": [
            {
                "description": "XDS110 Class Auxiliary Data Port",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM8",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM8",
            },
            {
                "description": "XDS110 Class Application/User UART",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM6",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM6",
            },
        ],
        "uart_port": "COM6",
        "ports": ["COM6", "COM8"],
    },
    {
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "winnt",
            "kernelVersion": "10.0.22631",
            "prettyProductName": "Windows 11 Version 23H2",
            "productType": "windows",
            "productVersion": "11",
        },
        "available_ports": [
            {
                "description": "XDS110 Class Auxiliary Data Port",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM7",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM7",
            },
            {
                "description": "XDS110 Class Application/User UART",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM6",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM6",
            },
        ],
        "uart_port": "COM6",
        "ports": ["COM6", "COM7"],
    },
    {
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "winnt",
            "kernelVersion": "10.0.22631",
            "prettyProductName": "Windows 11 Version 23H2",
            "productType": "windows",
            "productVersion": "11",
        },
        "available_ports": [
            {
                "description": "XDS110 Class Auxiliary Data Port",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM4",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM4",
            },
            {
                "description": "XDS110 Class Application/User UART",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM3",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM3",
            },
        ],
        "uart_port": "COM3",
        "ports": ["COM3", "COM4"],
    },
    {  # artificial example COM9, COM10
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "winnt",
            "kernelVersion": "10.0.22631",
            "prettyProductName": "Windows 11 Version 23H2",
            "productType": "windows",
            "productVersion": "11",
        },
        "available_ports": [
            {
                "description": "XDS110 Class Auxiliary Data Port",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM10",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM10",
            },
            {
                "description": "XDS110 Class Application/User UART",
                "manufacturer": "Texas Instruments Incorporated",
                "portName": "COM9",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM9",
            },
        ],
        "uart_port": "COM9",
        "ports": ["COM9", "COM10"],
    },
    {  # order reversed (North)
        "sys_info": {
            "currentCpuArchitecture": "x86_64",
            "kernelType": "winnt",
            "kernelVersion": "10.0.22631",
            "prettyProductName": "Windows 11 Version 23H2",
            "productType": "windows",
            "productVersion": "11",
        },
        "available_ports": [
            {
                "description": "Serielles USB-Gerät",
                "manufacturer": "Microsoft",
                "portName": "COM3",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM3",
            },
            {
                "description": "Serielles USB-Gerät",
                "manufacturer": "Microsoft",
                "portName": "COM4",
                "productIdentifier": 48_883,
                "vendorIdentifier": 1_105,
                "serialNumber": "MG350001",
                "systemLocation": "\\\\.\\COM4",
            },
        ],
        "uart_port": "COM4",
        "ports": ["COM3", "COM4"],
    },
]


@pytest.fixture(params=examples)
def example(request):
    return request.param


@pytest.fixture()
def available_ports(example):
    return [
        PortInfo(
            name=pi["portName"],
            vid=pi.get("vendorIdentifier", 0),
            pid=pi.get("productIdentifier", 0),
        )
        for pi in example["available_ports"]
    ]


def test_find_launchpad(example, available_ports):
    port_infos = launchpad.find_launchpad(available_ports)
    assert len(port_infos) == 2

    names = [pi.name for pi in port_infos]
    assert names == example["ports"]


def test_find_tiva_launchpad():
    available_ports = [
        PortInfo("COM0", launchpad.ti_vid, launchpad.tiva_pid),
        PortInfo("COM1", launchpad.ti_vid, launchpad.lp_pid),
    ]
    port_infos = launchpad.find_tiva_launchpad(available_ports)

    names = [pi.name for pi in port_infos]
    assert names == ["COM0"]
