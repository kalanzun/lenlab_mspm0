from itertools import batched

from PySide6.QtCore import QObject, Signal, Slot

from lenlab.launchpad.terminal import Terminal

from ..launchpad.protocol import pack
from ..singleshot import SingleShotTimer

START = pack(b"vstrt")
NEXT = pack(b"vnext")
STOP = pack(b"vstop")
ERROR = pack(b"verr!")


class Voltmeter(QObject):
    terminal: Terminal

    new_point = Signal(float, float, float)

    def __init__(self):
        super().__init__()
        self.offset = 0.0
        self.points = list()

        self.command_queue = list()
        self.busy = False
        self.stop_requested = False

        self.next_timer = SingleShotTimer(self.on_next_timeout, interval=200)

    @Slot(Terminal)
    def set_terminal(self, terminal: Terminal):
        self.terminal = terminal
        self.terminal.reply.connect(self.on_reply)

    @Slot()
    def start(self):
        if self.points:
            self.offset = self.points[-1][0] + 1
        else:
            self.offset = 0.0

        self.stop_requested = False
        self.command(START)

    @Slot()
    def stop(self):
        self.next_timer.stop()
        self.stop_requested = True
        self.command(STOP)

    @Slot()
    def reset(self):
        del self.points[:]

    def next_command(self):
        if not self.busy and self.command_queue:
            command = self.command_queue.pop(0)
            self.terminal.write(command)
            self.busy = True

    def command(self, command: bytes):
        self.command_queue.append(command)
        self.next_command()

    @Slot(bytes)
    def on_reply(self, reply: bytes):
        self.busy = False

        if reply == START:
            if not self.stop_requested:
                self.next_timer.start()

        elif reply[1:2] == b"v" and (reply[4:8] == b" red" or reply[4:8] == b" blu"):
            self.add_points(reply)
            if not self.stop_requested:
                self.next_timer.start()

        elif reply == STOP:
            pass

        elif reply == ERROR:
            print("Error reply")

        else:
            print(reply)
            raise AssertionError()

    @Slot()
    def on_next_timeout(self):
        self.command(NEXT)

    def add_points(self, reply: bytes):
        for point in batched(reply[8:], 8):
            time = int.from_bytes(point[:4], byteorder="little") * 1.0 + self.offset
            value1 = int.from_bytes(point[4:6], byteorder="little") / 2**12 * 3.3
            value2 = int.from_bytes(point[6:8], byteorder="little") / 2**12 * 3.3
            self.points.append([time, value1, value2])
            self.new_point.emit(time, value1, value2)
