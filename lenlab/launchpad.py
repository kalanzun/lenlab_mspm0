from enum import IntEnum, auto

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


class LpError(IntEnum):
    MORE_THAN_ONE_LAUNCHPAD_FOUND = auto()
    TIVA_LAUNCHPAD_FOUND = auto()
    NO_LAUNCHPAD_FOUND = auto()
    PERMISSION_ERROR = auto()
    RESOURCE_ERROR = auto()
    UNEXPECTED_ERROR = auto()


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

    assert len(matches) < 2, LpError.MORE_THAN_ONE_LAUNCHPAD_FOUND
    assert not find_vid_pid(port_infos, 0x1CBE, 0x00FD), LpError.TIVA_LAUNCHPAD_FOUND
    assert None, LpError.NO_LAUNCHPAD_FOUND


class Launchpad(QObject):
    ready = Signal()
    error = Signal(LpError)
    reply = Signal(bytes)
    bsl_reply = Signal(bytes)

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.errorOccurred.connect(self.on_error_occurred)
        self.port.readyRead.connect(self.on_ready_read)

    @Slot(bool)
    def retry(self, flag: bool):
        if self.port.isOpen():
            self.port.close()

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
                self.ready.emit()

        except AssertionError as error:
            self.error.emit(error.args[0])

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(LpError.PERMISSION_ERROR)
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(LpError.RESOURCE_ERROR)
        else:
            self.error.emit(LpError.UNEXPECTED_ERROR)

    @Slot()
    def on_ready_read(self):
        n = self.port.bytesAvailable()
        if n == 1:
            ack = self.port.read(1).data()
            self.bsl_reply.emit(ack)
        elif n >= 8:
            head = self.port.peek(4).data()
            length = head[2] + (head[3] << 8)
            if n >= length + 8:
                message = self.port.read(length + 8).data()
                if message[0] == 0 and message[1] == 8:
                    self.bsl_reply.emit(message)
                else:
                    self.reply.emit(message)
                if n > length + 8:
                    self.on_ready_read()
