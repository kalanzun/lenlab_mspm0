from PySide6.QtCore import QIODeviceBase, QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from .message import Message


def find_vid_pid(
    port_infos: list[QSerialPortInfo], vid: int, pid: int
) -> list[QSerialPortInfo]:
    return [
        port_info
        for port_info in port_infos
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid
    ]


class Launchpad(QObject):
    ready = Signal()
    error = Signal(Message)
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

        matches = find_vid_pid(port_infos, 0x0451, 0xBEF3)
        if len(matches) == 2:
            aux_port_info, port_info = matches
            self.port.setPort(port_info)

            # open emits a NoError on errorOccurred in any case
            # in case of an error, it emits errorOccurred a second time with the error
            # on_error_occurred handles the error case
            if self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite):
                self.ready.emit()

        elif len(matches) > 2:
            self.error.emit(TooManyLaunchpadsFound(len(matches) // 2))

        elif find_vid_pid(port_infos, 0x1CBE, 0x00FD):
            self.error.emit(TivaLaunchpadFound())

        else:
            self.error.emit(NoLaunchpadFound())

    @Slot(QSerialPort.SerialPortError)
    def on_error_occurred(self, error):
        if error is QSerialPort.SerialPortError.NoError:
            pass
        elif error is QSerialPort.SerialPortError.PermissionError:
            self.error.emit(LaunchpadPermissionError())
        elif error is QSerialPort.SerialPortError.ResourceError:
            self.error.emit(LaunchpadResourceError())
        else:
            self.error.emit(LaunchpadCommunicationError(self.port.errorString()))

    @Slot()
    def on_ready_read(self):
        n = self.port.bytesAvailable()
        if n == 1:
            ack = self.port.read(1).data()
            self.bsl_reply.emit(ack)
        elif n >= 8:
            head = self.port.peek(4).data()
            length = 8 + head[2] + (head[3] << 8)
            if n >= length:
                message = self.port.read(length).data()
                if message[0] == 0 and message[1] == 8:
                    self.bsl_reply.emit(message)
                else:
                    self.reply.emit(message)
                if n > length:
                    self.on_ready_read()


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
