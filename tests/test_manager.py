import pytest

from lenlab.manager import PortManager, PortInfo


class Monitor:
    def __init__(self):
        self.args = list()

    @property
    def count(self):
        return len(self.args)

    def __call__(self, *args):
        self.args.append(args)


@pytest.mark.launchpad
def test_open_launchpad():
    manager = PortManager()
    manager.ready.connect(ready := Monitor())
    manager.error.connect(error := Monitor())
    manager.open_launchpad()
    assert ready.count == 1
    assert error.count == 0


def test_no_launchpad():
    manager = PortManager()
    manager.ready.connect(ready := Monitor())
    manager.error.connect(error := Monitor())
    manager.open_launchpad([])
    assert ready.count == 0
    assert error.count == 1


@pytest.mark.launchpad
def test_duplicate():
    manager = PortManager()
    manager.ready.connect(ready := Monitor())
    manager.error.connect(error := Monitor())
    manager.open_launchpad()
    assert ready.count == 1
    assert error.count == 0

    manager2 = PortManager()
    manager2.ready.connect(ready2 := Monitor())
    manager2.error.connect(error2 := Monitor())
    manager2.open_launchpad()
    assert ready2.count == 0
    assert error2.count == 1


def test_tiva_launchpad():
    manager = PortManager()
    manager.ready.connect(ready := Monitor())
    manager.error.connect(error := Monitor())
    manager.open_launchpad([PortInfo(0x1CBE, 0x00FD)])
    assert ready.count == 0
    assert error.count == 1
