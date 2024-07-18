import pytest

from PySide6.QtSerialPort import QSerialPortInfo

from lenlab.launchpad import Launchpad


class PortInfo(QSerialPortInfo):
    def __init__(self, vid, pid):
        super().__init__()

        self.vid = vid
        self.pid = pid

    def vendorIdentifier(self):
        return self.vid

    def productIdentifier(self):
        return self.pid


class Monitor:
    def __init__(self):
        self.args = list()

    @property
    def count(self):
        return len(self.args)

    def __call__(self, *args):
        self.args.append(args)


@pytest.fixture
def lp():
    return Launchpad()


@pytest.fixture
def ready(lp):
    lp.ready.connect(ready := Monitor())
    return ready


@pytest.fixture
def error(lp):
    lp.error.connect(error := Monitor())
    return error


@pytest.mark.launchpad
def test_open_launchpad(lp, ready, error):
    lp.open_launchpad()
    assert ready.count == 1
    assert error.count == 0


def test_no_launchpad(lp, ready, error):
    lp.open_launchpad([])
    assert ready.count == 0
    assert error.count == 1


@pytest.mark.launchpad
def test_duplicate(lp, ready, error):
    lp.open_launchpad()
    assert ready.count == 1
    assert error.count == 0

    lp2 = Launchpad()
    lp2.ready.connect(ready2 := Monitor())
    lp2.error.connect(error2 := Monitor())
    lp2.open_launchpad()
    assert ready2.count == 0
    assert error2.count == 1


def test_tiva_launchpad(lp, ready, error):
    lp.open_launchpad([PortInfo(0x1CBE, 0x00FD)])
    assert ready.count == 0
    assert error.count == 1
