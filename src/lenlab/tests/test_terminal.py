import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtSerialPort import QSerialPortInfo
from PySide6.QtTest import QSignalSpy

from lenlab.terminal import Terminal, create_single_shot_timer, pack


class Spy(QSignalSpy):
    def get_single(self):
        if self.count() == 1:
            return self.at(0)[0]


class App(QCoreApplication):
    def __init__(self):
        super().__init__()

        self.timer = create_single_shot_timer(self.quit)

    def run(self, timeout=100):
        self.timer.start(timeout)
        self.exec()

    def wait_for(self, signal, timeout=100):
        spy = Spy(signal)
        signal.connect(self.quit)
        self.run(timeout)

        return spy.get_single()


@pytest.fixture(scope="session")
def app() -> App:
    return App()


@pytest.fixture(scope="session")
def terminal() -> Terminal:
    terminal = Terminal()
    port_infos = QSerialPortInfo.availablePorts()
    terminal.open(port_infos)
    yield terminal
    terminal.close()


def test_bsl_connect(app: App, terminal: Terminal):
    if not terminal.port_open:
        pytest.skip("no port")

    terminal.write(bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE)))
    reply = app.wait_for(terminal.data)

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


def test_firmware_knock(app: App, terminal: Terminal):
    if not terminal.port_open:
        pytest.skip("no port")

    terminal.write(pack(b"knock"))
    reply = app.wait_for(terminal.data)

    assert reply is not None
    assert len(reply) == 8
    assert reply.startswith(b"Lk\x00\x00")
