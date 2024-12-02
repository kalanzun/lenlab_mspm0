from time import sleep

import numpy as np
import pytest

from lenlab.launchpad.protocol import pack, pack_uint32
from lenlab.launchpad.terminal import Terminal
from lenlab.model.lenlab import Lenlab
from lenlab.model.voltmeter import Voltmeter, VoltmeterPoint, VoltmeterSaveError
from lenlab.spy import Spy


def test_voltmeter(firmware, terminal: Terminal):
    print("")

    spy = Spy(terminal.reply)
    terminal.write(pack_uint32(b"v", 20))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"vstrt")

    for i in range(10):
        sleep(0.1)
        spy = Spy(terminal.reply)
        terminal.write(pack(b"vnext"))
        reply = spy.run_until_single_arg()
        assert reply is not None, str(i)
        print(reply)
        if i % 2 == 0:
            assert reply[4:8] == b" red"
        else:
            assert reply[4:8] == b" blu"

    spy = Spy(terminal.reply)
    terminal.write(pack(b"vstop"))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"vstop")


def test_overflow(firmware, terminal: Terminal):
    """test recovery after overflow"""
    print("")

    spy = Spy(terminal.reply)
    terminal.write(pack_uint32(b"v", 20))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"vstrt")

    sleep(3)

    spy = Spy(terminal.reply)
    terminal.write(pack(b"vnext"))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"verr!")

    spy = Spy(terminal.reply)
    terminal.write(pack_uint32(b"v", 20))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"vstrt")

    for i in range(10):
        sleep(0.1)
        spy = Spy(terminal.reply)
        terminal.write(pack(b"vnext"))
        reply = spy.run_until_single_arg()
        print(reply)
        if i % 2 == 0:
            assert reply[4:8] == b" red"
        else:
            assert reply[4:8] == b" blu"

    spy = Spy(terminal.reply)
    terminal.write(pack(b"vstop"))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
    assert reply == pack(b"vstop")


@pytest.fixture()
def voltmeter():
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    return voltmeter


@pytest.fixture()
def points(voltmeter):
    voltmeter.points = [VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3)]
    voltmeter.unsaved = True


def test_save_as(tmp_path, voltmeter, points):
    file_path = tmp_path / "voltmeter.csv"
    assert voltmeter.save_as(str(file_path))

    assert voltmeter.unsaved is False
    data = np.loadtxt(file_path, delimiter=";", skiprows=2)
    # a list of rows
    example = np.array([(float(i), i / 10, i / 100) for i in range(3)])
    assert np.all(data == example)


def test_save_as_empty(tmp_path, voltmeter):
    file_path = tmp_path / "voltmeter.csv"
    assert voltmeter.save_as(str(file_path))

    head = file_path.read_text()
    assert head.startswith("Lenlab")
    assert len(head.splitlines()) == 2


def test_save_as_permission_error(tmp_path, voltmeter, points):
    voltmeter.auto_save = True

    spy = Spy(voltmeter.error)
    assert not voltmeter.save_as(str(tmp_path))  # cannot save in a directory

    error = spy.get_single_arg()
    assert isinstance(error, VoltmeterSaveError)

    assert voltmeter.unsaved is True
    assert voltmeter.auto_save is False


def test_voltmeter_point_index_access():
    point = VoltmeterPoint(1.0, 2.0, 3.0)
    assert point[0] == 2.0
    assert point[1] == 3.0
    with pytest.raises(IndexError):
        assert point[3] == 4.0


def test_discard(voltmeter, points):
    voltmeter.discard()

    assert not voltmeter.points
    assert voltmeter.unsaved is False


@pytest.fixture()
def saved(tmp_path, voltmeter):
    file_path = tmp_path / "voltmeter.csv"
    assert voltmeter.save_as(str(file_path))
    return file_path


def test_auto_save(voltmeter, points, saved):
    saved.unlink()
    voltmeter.set_auto_save(True)
    assert voltmeter.auto_save is True
    assert not saved.exists(), "set auto save with no new points shall not write to the file"


def test_set_auto_save_with_new_points(voltmeter, points, saved):
    voltmeter.points.extend([VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3, 6)])
    voltmeter.unsaved = True

    voltmeter.set_auto_save(True)
    assert voltmeter.auto_save is True
    assert voltmeter.unsaved is False

    data = np.loadtxt(saved, delimiter=";", skiprows=2)
    # a list of rows
    example = np.array([(float(i), i / 10, i / 100) for i in range(6)])
    assert np.all(data == example)


def test_auto_save_on_new_points(voltmeter, points, saved):
    voltmeter.set_auto_save(True)
    voltmeter.points.extend([VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3, 8)])
    voltmeter.unsaved = True
    # new_last_point calls save is a queued connection
    voltmeter.save()

    assert voltmeter.auto_save is True
    # assert voltmeter.unsaved is False

    data = np.loadtxt(saved, delimiter=";", skiprows=2)
    # a list of rows
    example = np.array([(float(i), i / 10, i / 100) for i in range(8)])
    assert np.all(data == example)


def test_no_auto_save_on_few_new_points(voltmeter, points, saved):
    voltmeter.set_auto_save(True)
    voltmeter.points.extend([VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3, 6)])
    voltmeter.unsaved = True

    saved.unlink()
    # new_last_point calls save is a queued connection
    voltmeter.save()

    assert voltmeter.auto_save is True
    assert voltmeter.unsaved is True

    assert not saved.exists()


def test_no_auto_save_on_no_new_points(voltmeter, points, saved):
    voltmeter.set_auto_save(True)
    saved.unlink()
    # new_last_point calls save is a queued connection
    voltmeter.save()

    assert voltmeter.auto_save is True
    assert voltmeter.unsaved is False

    assert not saved.exists()


def test_auto_save_on_discard(voltmeter, points, saved):
    voltmeter.set_auto_save(True)
    voltmeter.points.extend([VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3, 6)])
    voltmeter.unsaved = True

    voltmeter.discard()

    assert not voltmeter.points
    assert voltmeter.unsaved is False
    assert voltmeter.auto_save is False

    data = np.loadtxt(saved, delimiter=";", skiprows=2)
    # a list of rows
    example = np.array([(float(i), i / 10, i / 100) for i in range(6)])
    assert np.all(data == example)


def test_auto_save_permission_error(tmp_path, voltmeter, points, saved):
    voltmeter.set_auto_save(True)
    voltmeter.points.extend([VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3, 8)])
    voltmeter.unsaved = True

    voltmeter.file_name = str(tmp_path)  # cannot save in a directory
    spy = Spy(voltmeter.error)
    # new_last_point calls save is a queued connection
    voltmeter.save()

    error = spy.get_single_arg()
    assert isinstance(error, VoltmeterSaveError)

    assert voltmeter.unsaved is True
    assert voltmeter.auto_save is False
