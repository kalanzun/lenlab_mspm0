from typing import Iterable

from PySide6.QtCore import (
    QIODeviceBase,
    QObject,
    Signal,
    Slot,
)
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from .message import Message
from .singleshot import SingleShotTimer


def pack(payload: bytes) -> bytes:
    assert len(payload) == 5
    return b"L" + payload[0:1] + b"\x00\x00" + payload[1:]


def find_vid_pid(
    port_infos: Iterable[QSerialPortInfo], vid: int, pid: int
) -> Iterable[QSerialPortInfo]:
    for port_info in port_infos:
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid:
            yield port_info


class Terminal(QObject):
    """
    A data packet is a stream of bytes followed by a pause of at least 20 ms (about 20 bytes at 9600 baud).
    """

    data = Signal(bytes)
    reply = Signal(bytes)

    ready = Signal()
    error = Signal(Message)

    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.port.readyRead.connect(self.on_ready_read)
        self.port.errorOccurred.connect(self.on_error_occurred)

        # the OS might delay a chunk, < 50 ms doesn't always work
        # 50 ms: 3 error in 1000 packet transmissions, 30 KB packets
        self.timer = SingleShotTimer(self.on_timeout, 250)

    def open(self, port_infos: Iterable[QSerialPortInfo]) -> bool:
        matches = list(find_vid_pid(port_infos, 0x0451, 0xBEF3))
        if len(matches) == 2:
            aux_port_info, port_info = matches
            self.port.setPort(port_info)

            # open emits a NoError on errorOccurred in any case
            # in case of an error, it emits errorOccurred a second time with the error
            # on_error_occurred handles the error case
            if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                self.port.setBaudRate(QSerialPort.BaudRate.Baud9600)
                self.port.setDataBits(QSerialPort.DataBits.Data8)
                self.port.setFlowControl(QSerialPort.FlowControl.NoFlowControl)
                self.port.setParity(QSerialPort.Parity.NoParity)
                self.port.setStopBits(QSerialPort.StopBits.OneStop)

                self.ready.emit()
                return True

        elif len(matches) > 2:
            self.error.emit(TooManyLaunchpadsFound(len(matches) // 2))

        elif list(find_vid_pid(port_infos, 0x1CBE, 0x00FD)):
            self.error.emit(TivaLaunchpadFound())

        else:
            self.error.emit(NoLaunchpadFound())

        return False

    def close(self) -> None:
        self.port.close()

    @Slot()
    def on_ready_read(self) -> None:
        n = self.port.bytesAvailable()
        if n >= 8:
            head = self.port.peek(4).data()
            if head[0:1] == b"L" or head[0:2] == b"\x00\x08":
                length = int.from_bytes(head[2:4], "little") + 8
                if n >= length:
                    self.timer.stop()
                    n -= length
                    reply = self.port.read(length).data()
                    self.reply.emit(reply)

        if n > 0:
            self.timer.start()

    @Slot()
    def on_timeout(self) -> None:
        data = self.port.readAll().data()
        self.data.emit(data)

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error) -> None:
        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(LaunchpadPermissionError())
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(LaunchpadResourceError())
        else:
            self.error.emit(LaunchpadCommunicationError(self.port.errorString()))

    def write(self, packet: bytes) -> int:
        return self.port.write(packet)


class TooManyLaunchpadsFound(Message):
    english = """Too many Launchpads found: {0}
        Lenlab can only control one Launchpad at a time.
        Please connect a single Launchpad only."""
    german = """Zu viele Launchpads gefunden: {0}
        Lenlab kann nur ein Launchpad gleichzeitig steuern.
        Bitte nur ein einzelnes Launchpad verbinden."""


class TivaLaunchpadFound(Message):
    english = """Tiva C-Series Launchpad found
        This Lenlab Version 8 works with the Launchpad LP-MSPM0G3507.
        Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
        works with the Tiva C-Series Launchpad EK-TM4C123GXL."""
    german = """Tiva C-Serie Launchpad gefunden
        Dieses Lenlab in Version 8 funktioniert mit dem Launchpad LP-MSPM0G3507.
        Lenlab Version 7 (https://github.com/kalanzun/red_lenlab)
        funktioniert mit dem Tiva C-Serie Launchpad EK-TM4C123GXL."""


class NoLaunchpadFound(Message):
    english = """No Launchpad found
        Please connect the Launchpad via USB to the computer."""
    german = """Kein Launchpad gefunden
        Bitte das Launchpad über USB mit dem Computer verbinden."""


class LaunchpadPermissionError(Message):
    english = """Permission error on Launchpad connection
        Lenlab requires unique access to the serial communication with the Launchpad.
        Maybe another instance of Lenlab is running and blocks the access?"""
    german = """Keine Zugriffsberechtigung auf die Verbindung mit dem Launchpad
        Lenlab braucht alleinigen Zugriff auf die serielle Kommunikation mit dem Launchpad.
        Vielleicht läuft noch eine andere Instanz von Lenlab und blockiert den Zugriff?"""


class LaunchpadResourceError(Message):
    english = """Connection lost
        The Launchpad vanished. Please reconnect it to the computer."""
    german = """Verbindung verloren
        Das Launchpad ist verschwunden. Bitte wieder mit dem Computer verbinden."""


class LaunchpadCommunicationError(Message):
    english = "Communication error\n{0}"
    german = "Kommunikationsfehler\n{0}"
