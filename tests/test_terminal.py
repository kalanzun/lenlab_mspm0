from typing import Iterable

import pytest

from PySide6.QtCore import QObject, QTimer, QMetaMethod, QCoreApplication
from PySide6.QtTest import QSignalSpy

from lenlab.terminal import Terminal, Probe, packet


class Bot(QObject):
    def __init__(self, app: QCoreApplication, terminal: Terminal):
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
        self.terminal.write(data)

    def wait_for_transmission(self, timeout: int = 200) -> bool:
        return self.terminal.wait_for_transmission(timeout)

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

    def wait_for_bsl_ack_reply(
        self, timeout: int = 200
    ) -> (bytes | None, bytes | None):
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


@pytest.fixture(scope="module")
def terminal(app) -> Terminal:
    terminal = Terminal()
    if terminal.open():
        probe = Probe(terminal)
        probe.ready.connect(app.quit)
        probe.error.connect(app.quit)
        probe.start()
        app.exec()
        del probe

    yield terminal

    terminal.close()


@pytest.fixture
def bot(app: QCoreApplication, terminal: Terminal) -> Bot:
    return Bot(app, terminal)


@pytest.fixture
def bsl(bot: Bot) -> Bot:
    if not bot.terminal.bsl:
        pytest.skip("bsl required")

    return bot


@pytest.fixture
def firmware(bot: Bot) -> Bot:
    if not bot.terminal.firmware:
        pytest.skip("firmware required")

    return bot


def test_knock(firmware: Bot):
    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_incomplete_packet(firmware: Bot):
    firmware.write(b"L\x05\x00")
    assert firmware.wait_for_reply() is None

    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_wrong_baudrate(firmware: Bot):
    firmware.terminal.port.setBaudRate(4_000_000)
    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() is None

    firmware.terminal.port.setBaudRate(9_600)
    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_hitchhiker(firmware: Bot):
    firmware.write(packet(b"knock") + b"knock")
    assert firmware.wait_for_reply() == packet(b"hello")
    assert firmware.wait_for_reply() is None

    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_reply_too_long(firmware: Bot):
    firmware.write(packet(b"get10"))
    assert firmware.wait_for_reply() == packet(b"get10")
    assert firmware.wait_for_reply() is None

    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_baudrate(firmware: Bot):
    firmware.write(packet(b"b4MBd"))
    assert firmware.wait_for_transmission()

    firmware.terminal.port.setBaudRate(4_000_000)
    assert firmware.wait_for_reply(300) == packet(b"b4MBd")

    firmware.write(packet(b"knock"))
    assert firmware.wait_for_reply() == packet(b"hello")

    firmware.write(packet(b"b9600"))
    assert firmware.wait_for_transmission()

    firmware.terminal.port.setBaudRate(9_600)
    assert firmware.wait_for_reply(300) == packet(b"b9600")


def test_probe(firmware: Bot):
    firmware.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert firmware.wait_for_reply() == packet(b"hello")


def test_probe_bsl(bsl: Bot):
    bsl.write(bytes.fromhex("80 01 00 12 3A 61 44 DE"))
    assert bsl.wait_for_bsl_reply() == bytes.fromhex("08 02 00 3B 06 0D A7 F7 6B")
