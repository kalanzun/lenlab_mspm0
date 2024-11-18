from time import sleep

from lenlab.launchpad.protocol import pack
from lenlab.launchpad.terminal import Terminal
from lenlab.spy import Spy


def test_voltmeter(firmware, terminal: Terminal):
    print("")

    spy = Spy(terminal.reply)
    terminal.write(pack(b"vstrt"))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)

    for i in range(3):
        sleep(1)
        spy = Spy(terminal.reply)
        terminal.write(pack(b"vnext"))
        reply = spy.run_until_single_arg()
        assert reply is not None, str(i)
        print(reply)

    spy = Spy(terminal.reply)
    terminal.write(pack(b"vstop"))
    reply = spy.run_until_single_arg()
    assert reply is not None
    print(reply)
