from dataclasses import dataclass

from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


@dataclass
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

    assert len(matches) < 2, "MORE_THAN_ONE_LAUNCHPAD_FOUND"
    assert not [
        x for x in port_infos if x.vid == 0x1CBE and x.pid == 0x00FD
    ], "TIVA_LAUNCHPAD_FOUND"
    assert None, "NO_LAUNCHPAD_FOUND"


class PortManager(QObject):
    error = Signal(str)
    ready = Signal()

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.errorOccurred.connect(self.on_error_occurred)

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
            self.error.emit(str(error))

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if error is QSerialPort.SerialPortError.NoError:
            return

        self.error.emit(str(error))
