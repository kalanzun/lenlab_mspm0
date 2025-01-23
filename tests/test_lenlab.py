from lenlab.device.lenlab import Lenlab
from lenlab.launchpad.discovery import Discovery


def test_lenlab_startup(monkeypatch):
    monkeypatch.setattr(Discovery, "find", lambda self: None)
    lenlab = Lenlab()
    lenlab.on_startup()
