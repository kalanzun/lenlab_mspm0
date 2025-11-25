import pytest

from lenlab.app.voltmeter import VoltmeterWidget


@pytest.fixture()
def voltmeter(qt_widgets, lenlab):
    return VoltmeterWidget(lenlab)


def test_start(voltmeter, terminal):
    voltmeter.on_start_clicked()
    assert voltmeter.started
    assert voltmeter.polling

    command = terminal.get_single_command()
    assert command.startswith(b"Lv")


def test_save_as(voltmeter, terminal, save_as_output):
    voltmeter.on_save_as_clicked()
    content = save_as_output["file_path"].read_text(encoding="utf-8")
    assert content.startswith("Lenlab_MSPM0,8.6,voltmeter\ntime,channel1,channel2\n")


def test_save_image(voltmeter, terminal, save_as_output):
    voltmeter.on_save_image_clicked()
    content = save_as_output["file_path"].read_text(encoding="utf-8")
    assert content.startswith(
        '<?xml version="1.0" encoding="utf-8" standalone="no"?>\n'
        '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"'
    )
