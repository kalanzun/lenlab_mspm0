from typing import Iterable

from PySide6.QtCore import QObject, QTimer, Signal, Slot, QIODeviceBase
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


PortInfoIterable = Iterable[QSerialPortInfo]


def find_vid_pid(port_infos: PortInfoIterable, vid: int, pid: int) -> PortInfoIterable:
    for port_info in port_infos:
        if port_info.vendorIdentifier() == vid and port_info.productIdentifier() == pid:
            yield port_info


def packet(cmd: bytes):
    assert len(cmd) == 5
    return b"L\x01\x00" + cmd


class BaseTerminal(QObject):
    def __init__(self):
        super().__init__()

        self.port = QSerialPort()
        self.is_open = False

        self.firmware = False
        self.bsl = False
        self.no_reply = False

    def open(self) -> bool:
        port_infos = QSerialPortInfo.availablePorts()
        matches = list(find_vid_pid(port_infos, 0x0451, 0xBEF3))
        if len(matches) == 2:
            aux_port_info, port_info = matches
            self.port.setPort(port_info)
            self.port.setBaudRate(9600)
            self.is_open = self.port.open(QIODeviceBase.OpenModeFlag.ReadWrite)

        else:
            self.is_open = False

        return self.is_open

    def close(self) -> None:
        self.port.close()
        self.is_open = False

    def write(self, data: bytes):
        self.port.write(data)

    def wait_for_transmission(self, timeout: int = 200) -> bool:
        return self.port.waitForBytesWritten(timeout)


class Terminal(BaseTerminal):
    reply = Signal(bytes)
    bsl_ack = Signal(bytes)
    bsl_reply = Signal(bytes)

    def __init__(self):
        super().__init__()

        self.port.readyRead.connect(self.on_ready_read)
        # self.port.errorOccurred.connect(self.on_error_occurred)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.on_timeout)

    @Slot()
    def on_ready_read(self):
        n = self.port.bytesAvailable()
        if n >= 1:
            ack = self.port.peek(1).data()
            # a lengthy reply may not start with 0 or 0x51 - 0x56
            if ack in b"\x00QRSTUV":  # 0x51 - 0x56
                ack = self.port.read(1).data()
                n -= len(ack)
                self.bsl_ack.emit(ack)

        if n >= 7:
            head = self.port.peek(3).data()
            # Lenlab replies start with 'L' and BSL replies start with 8
            if head[0] in b"\x08L":
                length = int.from_bytes(head[1:3], byteorder="little") + 7
                if n >= length:
                    reply = self.port.read(length).data()
                    n -= len(reply)
                    if reply[0] == 8:
                        self.bsl_reply.emit(reply)
                    else:
                        self.reply.emit(reply)

        if n == 0:
            self.timer.stop()
        else:
            self.timer.start()

    @Slot()
    def on_timeout(self) -> None:
        self.port.readAll()


class Probe(QObject):
    ready = Signal(str)
    error = Signal(str)

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal

        self.terminal.reply.connect(self.on_reply)
        self.terminal.bsl_ack.connect(self.on_bsl_ack)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.on_timeout)

    def start(self) -> None:
        self.terminal.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
        self.timer.start()

    @Slot()
    def on_reply(self, reply: bytes) -> None:
        self.timer.stop()
        if reply == packet(b"hello"):
            self.terminal.firmware = True
            self.ready.emit("firmware")
        else:
            self.error.emit("invalid reply")

    @Slot()
    def on_bsl_ack(self, ack: bytes) -> None:
        if ack == b"\x00":
            self.terminal.bsl = True
            # a core response might follow
        else:
            self.timer.stop()
            self.error.emit("invalid ack")

    @Slot()
    def on_timeout(self) -> None:
        if self.terminal.bsl:
            self.ready.emit("bsl")
            # there was a BSL ack, but no core response
        else:
            self.terminal.no_reply = True
            self.ready.emit("no reply")


class SyncTerminal(BaseTerminal):
    def read(self) -> bytes:
        # do read extra data
        return self.port.readAll().data()

    def read_packet(self, timeout: int = 200) -> bytes | None:
        while self.port.waitForReadyRead(timeout):
            n = self.port.bytesAvailable()
            if n >= 1:
                ack = self.port.peek(1).data()
                # a lengthy reply may not start with 0 or 0x51 - 0x56
                if ack in b"\x00QRSTUV":  # 0x51 - 0x56
                    return self.port.read(1).data()

            if n >= 7:
                head = self.port.peek(3).data()
                # Lenlab replies start with 'L' and BSL replies start with 8
                if head[0] in b"\x08L":
                    length = int.from_bytes(head[1:3], byteorder="little") + 7
                    if n >= length:
                        return self.port.read(length).data()

        # timeout
        self.port.readAll()  # clear out partial packet data

    def probe(self) -> bool:
        self.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
        reply = self.read_packet()

        if reply == packet(b"hello"):
            self.firmware = True
            return True

        if reply == b"\x00":
            self.bsl = True

            # When someone connects a second time, the BSL sends a core response to the connect command
            response = self.read_packet(100)
            return not response or response == bytes.fromhex(
                "08 02 00 3B 06 0D A7 F7 6B"
            )

        if reply is None:
            self.no_reply = True
            return True

        return False  # invalid reply
