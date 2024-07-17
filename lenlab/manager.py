from dataclasses import dataclass

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from . import messages
from .messages import Category, Message


@dataclass(frozen=True)
class PortInfo:
    vid: int = 0
    pid: int = 0
    port_info: QSerialPortInfo | None = None

    @classmethod
    def available_ports(cls):
        return [
            cls(port_info.vendorIdentifier(), port_info.productIdentifier(), port_info)
            for port_info in QSerialPortInfo.availablePorts()
        ]


def find_launchpad(port_infos: list[PortInfo]) -> QSerialPortInfo:
    matches = [x for x in port_infos if x.vid == 0x0451 and x.pid == 0xBEF3]
    if len(matches) == 2:
        aux_port_info, app_port_info = matches
        return app_port_info.port_info

    assert len(matches) < 2, messages.MORE_THAN_ONE_LAUNCHPAD_FOUND
    assert not [
        x for x in port_infos if x.vid == 0x1CBE and x.pid == 0x00FD
    ], messages.TIVA_LAUNCHPAD_FOUND
    assert None, messages.NO_LAUNCHPAD_FOUND


class PortManager(QObject):
    error = Signal(Message)
    ready = Signal()

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.errorOccurred.connect(self.on_error_occurred)

    @Slot(bool)
    def retry(self):
        self.open_launchpad()

    def open_launchpad(self, port_infos: list[PortInfo] | None = None):
        if port_infos is None:
            port_infos = PortInfo.available_ports()

        try:
            self.port.setPort(find_launchpad(port_infos))

            # open emits a NoError on errorOccurred in any case
            # in case of an error, it emits errorOccurred a second time with the error
            # on_error_occurred handles the error case
            if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                self.ready.emit()

        except AssertionError as error:
            self.error.emit(error.args[0])

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if self.port.isOpen():
            self.port.close()

        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(messages.PERMISSION_ERROR)
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(messages.RESOURCE_ERROR)
        else:
            self.error.emit(Message(Category.ERROR, f"{error}\n"))
