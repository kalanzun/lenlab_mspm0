from pathlib import Path
from time import sleep

import numpy as np

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


def test_save_as(tmp_path):
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    voltmeter.points = [VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3)]
    voltmeter.unsaved = True
    assert voltmeter.save_as(str(tmp_path / "voltmeter.csv"))

    assert voltmeter.unsaved is False
    data = np.loadtxt(voltmeter.file_name, delimiter=";", skiprows=2)
    # a list of rows
    example = np.array([(float(i), i / 10, i / 100) for i in range(3)])
    assert np.all(data == example)


def test_save_as_empty(tmp_path):
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    assert voltmeter.save_as(str(tmp_path / "voltmeter.csv"))

    head = Path(voltmeter.file_name).read_text()
    assert head.startswith("Lenlab")
    assert len(head.splitlines()) == 2


def test_save_as_permission_error(tmp_path):
    lenlab = Lenlab()
    voltmeter = Voltmeter(lenlab)
    spy = Spy(voltmeter.error)
    voltmeter.points = [VoltmeterPoint(float(i), i / 10, i / 100) for i in range(3)]
    voltmeter.unsaved = True
    assert not voltmeter.save_as(str(tmp_path))  # cannot save in a directory

    assert voltmeter.unsaved is True
    assert spy.count() == 1
    error = spy.get_single_arg()
    assert isinstance(error, VoltmeterSaveError)
