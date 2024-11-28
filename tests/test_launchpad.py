import pytest

from lenlab.launchpad.launchpad import (
    find_call_up,
    find_vid_pid, find_launchpad,
)


class MockSerialPortInfo:
    def __init__(self, info: dict):
        self.info = info

    def vendorIdentifier(self):
        return self.info.get("vendorIdentifier", 0)

    def productIdentifier(self):
        return self.info.get("productIdentifier", 0)

    def portName(self):
        return self.info["portName"]

    def description(self):
        return self.info.get("description", "")


def windows_port_infos():
    yield {'description': 'XDS110 Class Auxiliary Data Port',
     'manufacturer': 'Texas Instruments Incorporated',
     'portName': 'COM3',
     'productIdentifier': 48_883,
     'vendorIdentifier': 1_105,
     'serialNumber': 'MG350001',
     'systemLocation': '\\\\.\\COM3'}
    yield {'description': 'XDS110 Class Application/User UART',
     'manufacturer': 'Texas Instruments Incorporated',
     'portName': 'COM4',
     'productIdentifier': 48_883,
     'vendorIdentifier': 1_105,
     'serialNumber': 'MG350001',
     'systemLocation': '\\\\.\\COM4'}


def windows_port_infos_extra():
    # additional port
    yield {
        "description": "Intel(R) Active Management Technology - SOL",
        "manufacturer": "Intel",
        "portName": "COM3",
        "productIdentifier": 31_467,
        "vendorIdentifier": 32_902,
        "serialNumber": "",
        "systemLocation": "\\\\.\\COM3",
    }
    yield {
        "description": "XDS110 Class Auxiliary Data Port",
        "manufacturer": "Texas Instruments Incorporated",
        "portName": "COM12",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "\\\\.\\COM12",
    }
    yield {
        "description": "XDS110 Class Application/User UART",
        "manufacturer": "Texas Instruments Incorporated",
        "portName": "COM11",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "\\\\.\\COM11",
    }


def windows_port_infos_blank_description():
    # without TI driver
    yield {
        "description": "",
        "manufacturer": "Texas Instruments Incorporated",
        "portName": "COM3",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "\\\\.\\COM1",
    }
    yield {
        "description": "",
        "manufacturer": "Texas Instruments Incorporated",
        "portName": "COM5",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "\\\\.\\COM2",
    }


def linux_port_infos():
    yield {
        "description": "XDS110  03.00.00.32  Embed with CMSIS-DAP",
        "manufacturer": "Texas Instruments",
        "portName": "ttyACM0",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/ttyACM0",
    }
    yield {
        "description": "XDS110  03.00.00.32  Embed with CMSIS-DAP",
        "manufacturer": "Texas Instruments",
        "portName": "ttyACM1",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/ttyACM1",
    }
    yield {"portName": "ttyS0"}
    yield {"portName": "ttyS1"}
    yield {"portName": "ttyS10"}
    yield {"portName": "ttyS11"}
    ...


def mac_arm64_port_infos():
    # tty and cu
    yield {"portName": "cu.Bluetooth - Incoming - Port"}
    yield {"portName": "tty.Bluetooth - Incoming - Port"}
    yield {
        "description": "USB ACM",
        "manufacturer": "Texas Instruments",
        "portName": "cu.usbmodemMG3500014",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/cu.usbmodemMG3500014",
    }
    yield {
        "description": "USB ACM",
        "manufacturer": "Texas Instruments",
        "portName": "tty.usbmodemMG3500014",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/tty.usbmodemMG3500014",
    }
    yield {
        "description": "USB ACM",
        "manufacturer": "Texas Instruments",
        "portName": "cu.usbmodemMG3500011",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/cu.usbmodemMG3500011",
    }
    yield {
        "description": "USB ACM",
        "manufacturer": "Texas Instruments",
        "portName": "tty.usbmodemMG3500011",
        "productIdentifier": 48_883,
        "vendorIdentifier": 1_105,
        "serialNumber": "MG350001",
        "systemLocation": "/dev/tty.usbmodemMG3500011",
    }


@pytest.fixture(
    params=[
        windows_port_infos,
        windows_port_infos_extra,
        windows_port_infos_blank_description,
        linux_port_infos,
        mac_arm64_port_infos,
    ]
)
def mock_port_infos(request):
    return [MockSerialPortInfo(info) for info in request.param()]


def test_find_call_up(mock_port_infos):
    matches = find_call_up(find_vid_pid(mock_port_infos))
    assert len(matches) == 2


def test_find_launchpad(mock_port_infos):
    matches = find_launchpad(mock_port_infos)
    assert len(matches) == 1 or len(matches) == 2
