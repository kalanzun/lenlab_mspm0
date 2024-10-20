from typing import Callable, Iterable

from PySide6.QtCore import (
    QIODeviceBase,
    QObject,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


def pack(payload: bytes) -> bytes:
    assert len(payload) == 5
    return b"L" + payload[0:1] + b"\x00\x00" + payload[1:]


def create_single_shot_timer(
    callback: Callable[[], None], timeout: int = 100
) -> QTimer:
    timer = QTimer()
    timer.setSingleShot(True)
    timer.setInterval(timeout)
    timer.timeout.connect(callback)
    return timer


def find_vid_pid(
    port_infos: Iterable[QSerialPortInfo], vid: int, pid: int
) -> Iterable[QSerialPortInfo]:
    for port_info in port_infos:
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid:
            yield port_info


class TerminalError(Exception):
    pass


class Terminal(QObject):
    """
    A data packet is a stream of bytes followed by a pause of at least 20 ms (about 20 bytes at 9600 baud).
    """

    data = Signal(bytes)
    error = Signal(TerminalError)

    port_open: bool = False

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.readyRead.connect(self.on_ready_read)
        self.port.errorOccurred.connect(self.on_error_occurred)

        self.timer = create_single_shot_timer(self.on_timeout, 20)

    def open(self, port_infos: Iterable[QSerialPortInfo]) -> bool:
        matches = list(find_vid_pid(port_infos, 0x0451, 0xBEF3))
        if len(matches) == 2:
            aux_port_info, port_info = matches
            self.port.setPort(port_info)
            self.port.setBaudRate(9600)
            # on_error_occurred will handle an error
            self.port_open = self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

        else:
            self.port_open = False
            self.error.emit(TerminalError("no port found"))

        return self.port_open

    def close(self) -> None:
        self.port.close()
        self.port_open = False

    @Slot()
    def on_ready_read(self) -> None:
        self.timer.start()

    @Slot()
    def on_timeout(self) -> None:
        data = self.port.readAll().data()
        self.data.emit(data)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error) -> None:
        if error == QSerialPort.SerialPortError.NoError:
            pass
        else:
            self.error.emit(TerminalError(error))

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)
