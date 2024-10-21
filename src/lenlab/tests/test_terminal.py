import pytest
from PySide6.QtCore import QCoreApplication, QEventLoop
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtTest import QSignalSpy

from lenlab.terminal import Terminal, create_single_shot_timer, pack


class Spy(QSignalSpy):
    def __init__(self, signal, timeout=100):
        super().__init__(signal)

        self._signal = signal
        self._timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            return

        if self.count() == 1:
            return

        loop = QEventLoop()
        self._signal.connect(loop.quit)
        timer = create_single_shot_timer(loop.quit, self._timeout)

        timer.start()
        loop.exec()
        self._signal.disconnect(loop.quit)

    def get_single(self):
        if self.count() == 1:
            return self.at(0)[0]


@pytest.fixture(scope="session", autouse=True)
def app() -> QCoreApplication:
    return QCoreApplication()


@pytest.fixture(scope="session")
def port_infos():
    return QSerialPortInfo.availablePorts()


@pytest.fixture
def terminal(port_infos) -> Terminal:
    terminal = Terminal()
    if not terminal.open(port_infos):
        pytest.skip("no port")

    yield terminal
    terminal.close()


def test_bsl_connect(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))

    reply = spy.get_single()
    assert reply is not None
    assert len(reply) in {1, 8, 10}

    # firmware
    if len(reply) == 8:
        assert reply.startswith(b"Lk\x00\x00")

    # bsl
    elif len(reply) == 1:
        assert reply == b"\x00"
    elif len(reply) == 10:
        assert reply == bytes(
            (0x00, 0x08, 0x02, 0x00, 0x3B, 0x06, 0x0D, 0xA7, 0xF7, 0x6B)
        )


def test_knock(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_hitchhiker(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock") + b"knock")

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    with Spy(terminal.data) as spy:
        pass

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_command_too_short(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(b"Lk\x05\x00")

    reply = spy.get_single()
    assert reply is None

    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"


def test_change_baudrate(terminal: Terminal):
    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    # with Spy(terminal.data) as spy:
    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b4MBd"))
    assert tx.get_single() == 8

    assert terminal.port.setBaudRate(4_000_000)
    assert terminal.port.clear()

    # reply = spy.get_single()
    # assert reply is None
    # assert reply == b"Lb\x00\x004MBd"

    with Spy(terminal.data) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"

    # with Spy(terminal.data) as spy:
    with Spy(terminal.port.bytesWritten) as tx:
        terminal.write(pack(b"b9600"))
    assert tx.get_single() == 8

    assert terminal.port.setBaudRate(9_600)
    assert terminal.port.clear()

    # reply = spy.get_single()
    # assert reply is None
    # assert reply == b"Lb\x00\x004MBd"

    with Spy(terminal.data, timeout=300) as spy:
        terminal.write(pack(b"knock"))

    reply = spy.get_single()
    assert reply == b"Lk\x00\x00nock"
