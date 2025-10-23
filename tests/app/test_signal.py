import pytest

from lenlab.app.signal import Frequency, SignalWidget
from lenlab.controller.lenlab import Lenlab


@pytest.fixture()
def lenlab():
    return Lenlab()


@pytest.fixture()
def signal(qt_widgets, lenlab):
    return SignalWidget(lenlab)


def test_create_command(signal):
    cmd = signal.create_command(b"a")
    assert cmd == b"La\x08\x00\xc8\x00\x00\x00\xd0\x07\x00\x00\x01\x00\x00\x00"


def test_amplitude(signal):
    signal.amplitude.slider.setValue(127)

    assert signal.amplitude.field.text() == "0.822 V"

    cmd = signal.create_command(b"a")
    assert cmd == b"La\x08\x00\xc8\x00\x00\x00\xd0\x07\xf8\x03\x01\x00\x00\x00"


def test_frequency(signal):
    signal.frequency.slider.setValue(105)

    assert signal.frequency.field.text() == "1.12 kHz"

    cmd = signal.create_command(b"a")
    assert cmd == b"La\x08\x00(\x00\x00\x00|\x03\x00\x00\x01\x00\x00\x00"


def test_harmonic(signal):
    signal.harmonic.slider.setValue(2)

    assert signal.harmonic.field.text() == "2"

    cmd = signal.create_command(b"a")
    assert cmd == b"La\x08\x00\xc8\x00\x00\x00\xd0\x07\x00\x00\x02\x00\x00\x00"


@pytest.mark.parametrize("a,b", [(123, "123 Hz"), (1230, "1.23 kHz"), (12300, "12.3 kHz")])
def test_frequency_format(a, b):
    assert Frequency.format_number(a) == b
