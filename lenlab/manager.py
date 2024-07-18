from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from . import messages
from .messages import Category, Message


def find_vid_pid(
    port_infos: list[QSerialPortInfo], vid: int, pid: int
) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


def find_launchpad(port_infos: list[QSerialPortInfo]) -> QSerialPortInfo:
    matches = find_vid_pid(port_infos, 0x0451, 0xBEF3)
    if len(matches) == 2:
        aux_port_info, app_port_info = matches
        return app_port_info

    assert len(matches) < 2, messages.MORE_THAN_ONE_LAUNCHPAD_FOUND
    assert not find_vid_pid(port_infos, 0x1CBE, 0x00FD), messages.TIVA_LAUNCHPAD_FOUND
    assert None, messages.NO_LAUNCHPAD_FOUND


class PortManager(QObject):
    message = Signal(Message)
    ready = Signal()

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.errorOccurred.connect(self.on_error_occurred)

    @Slot(bool)
    def retry(self):
        self.open_launchpad()

    def open_launchpad(self, port_infos: list[QSerialPortInfo] | None = None):
        if port_infos is None:
            port_infos = QSerialPortInfo.availablePorts()

        try:
            self.port.setPort(find_launchpad(port_infos))

            # open emits a NoError on errorOccurred in any case
            # in case of an error, it emits errorOccurred a second time with the error
            # on_error_occurred handles the error case
            if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                self.message.emit(messages.CONNECTED)
                self.ready.emit()

        except AssertionError as error:
            self.message.emit(error.args[0])

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if self.port.isOpen():
            self.port.close()

        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.message.emit(messages.PERMISSION_ERROR)
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.message.emit(messages.RESOURCE_ERROR)
        else:
            self.message.emit(Message(Category.ERROR, f"{error}\n"))
