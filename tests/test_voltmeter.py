from time import sleep

from lenlab.launchpad.protocol import pack, pack_uint32
from lenlab.launchpad.terminal import Terminal
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
