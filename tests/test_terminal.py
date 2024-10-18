from typing import Iterable

import pytest

from PySide6.QtCore import QObject, QTimer, QMetaMethod
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from lenlab.terminal import Terminal, packet


class Bot(QObject):
    def __init__(self, app: QApplication, terminal: Terminal):
        super().__init__()

        self.app = app
        self.terminal = terminal

        self.terminal.reply.connect(app.quit)
        self.terminal.bsl_reply.connect(app.quit)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(app.quit)

    @staticmethod
    def spy_items(obj: QObject) -> Iterable[tuple[str, QSignalSpy]]:
        meta = obj.metaObject()
        for i in range(meta.methodCount()):
            meth = meta.method(i)
            if meth.methodType() == QMetaMethod.MethodType.Signal:
                name = meth.name().data().decode()
                yield name, QSignalSpy(getattr(obj, name))

    def write(self, data: bytes) -> None:
        self.terminal.port.write(data)

    def wait_for_transmission(self, timeout: int = 200) -> bool:
        return self.terminal.port.waitForBytesWritten(timeout)

    def wait_for_reply(self, timeout: int = 200) -> bytes | None:
        spy = dict(self.spy_items(self.terminal))

        self.timer.start(timeout)
        self.app.exec()

        reply = spy["reply"]
        assert reply.count() <= 1

        assert spy["bsl_ack"].count() == 0
        assert spy["bsl_reply"].count() == 0

        return reply.at(0)[0] if reply.count() else None

    def wait_for_bsl_ack(self, timeout: int = 200) -> bytes | None:
        spy = dict(self.spy_items(self.terminal))

        self.terminal.bsl_ack.connect(self.app.quit)

        self.timer.start(timeout)
        self.app.exec()

        self.terminal.bsl_ack.disconnect(self.app.quit)

        assert spy["reply"].count() == 0

        bsl_ack = spy["bsl_ack"]
        assert bsl_ack.count() <= 1

        assert spy["bsl_reply"].count() == 0

        return bsl_ack.at(0)[0] if bsl_ack.count() else None

    def wait_for_bsl_ack_reply(self, timeout: int = 200) -> (bytes | None, bytes | None):
        spy = dict(self.spy_items(self.terminal))

        self.timer.start(timeout)
        self.app.exec()

        assert spy["reply"].count() == 0

        bsl_ack = spy["bsl_ack"]
        assert bsl_ack.count() <= 1

        bsl_reply = spy["bsl_reply"]
        assert bsl_reply.count() <= 1

        ack = bsl_ack.at(0)[0] if bsl_ack.count() else None
        reply = bsl_reply.at(0)[0] if bsl_reply.count() else None

        return ack, reply

    def wait_for_bsl_reply(self, timeout: int = 200) -> bytes:
        ack, reply = self.wait_for_bsl_ack_reply(timeout)
        assert ack == b"\x00"

        return reply


@pytest.fixture(scope="session")
def app() -> QApplication:
    return QApplication()


@pytest.fixture
def terminal(port) -> Terminal:
    return Terminal(port)


@pytest.fixture
def bot(app: QApplication, terminal: Terminal) -> Bot:
    return Bot(app, terminal)


def test_knock(firmware, bot: Bot):
    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_incomplete_packet(firmware, bot: Bot):
    bot.write(b"L\x05\x00")
    assert bot.wait_for_reply() is None

    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_wrong_baudrate(firmware, bot: Bot):
    bot.terminal.port.setBaudRate(4_000_000)
    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() is None

    bot.terminal.port.setBaudRate(9_600)
    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_hitchhiker(firmware, bot: Bot):
    bot.write(packet(b"knock") + b"knock")
    assert bot.wait_for_reply() == packet(b"hello")
    assert bot.wait_for_reply() is None

    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_reply_too_long(firmware, bot: Bot):
    bot.write(packet(b"get10"))
    assert bot.wait_for_reply() == packet(b"get10")
    assert bot.wait_for_reply() is None

    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_baudrate(firmware, bot: Bot):
    bot.write(packet(b"b4MBd"))
    assert bot.wait_for_transmission()

    bot.terminal.port.setBaudRate(4_000_000)
    assert bot.wait_for_reply(300) == packet(b"b4MBd")

    bot.write(packet(b"knock"))
    assert bot.wait_for_reply() == packet(b"hello")

    bot.write(packet(b"b9600"))
    assert bot.wait_for_transmission()

    bot.terminal.port.setBaudRate(9_600)
    assert bot.wait_for_reply(300) == packet(b"b9600")


def test_probe(firmware, bot: Bot):
    bot.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert bot.wait_for_reply() == packet(b"hello")


def test_probe_bsl(bsl, bot: Bot):
    bot.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert bot.wait_for_bsl_reply() == bytes.fromhex("08 02 00 3B 06 0D A7 F7 6B")
