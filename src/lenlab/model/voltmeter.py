import logging
from dataclasses import dataclass
from importlib import metadata
from itertools import batched
from typing import Self

from PySide6.QtCore import QIODevice, QObject, QSaveFile, Signal, Slot

from ..launchpad.protocol import pack, pack_uint32
from ..launchpad.terminal import Terminal
from ..message import Message
from ..singleshot import SingleShotTimer

logger = logging.getLogger(__name__)

START = pack(b"vstrt")
NEXT = pack(b"vnext")
STOP = pack(b"vstop")
ERROR = pack(b"verr!")


binary_second = 1000.0
binary_volt = 2**12 / 3.3


@dataclass(frozen=True, slots=True)
class VoltmeterPoint:
    time: float
    value1: float
    value2: float

    @classmethod
    def parse(cls, buffer: tuple, time_offset: float) -> Self:
        return cls(
            int.from_bytes(buffer[0:4], byteorder="little") / binary_second + time_offset,
            int.from_bytes(buffer[4:6], byteorder="little") / binary_volt,
            int.from_bytes(buffer[6:8], byteorder="little") / binary_volt,
        )

    def __getitem__(self, channel: int) -> float:
        match channel:
            case 0:
                return self.value1
            case 1:
                return self.value2
            case _:
                raise IndexError("VoltmeterPoint channel index out of range")

    def line(self):
        return f"{self.time:f}; {self.value1:f}; {self.value2:f};\n"


class Voltmeter(QObject):
    terminal: Terminal

    # rename to active?
    started_changed = Signal(bool)
    new_points = Signal(list)

    def __init__(self):
        super().__init__()
        self.interval = 0
        self.time_offset = 0.0
        self.points: list[VoltmeterPoint] = list()

        self.started = False
        self.unsaved = 0
        self.file_name = None
        self.auto_save = False

        # no reply timeout
        self.busy_timer = SingleShotTimer(self.on_busy_timeout, interval=2000)
        self.command_queue = list()
        self.retries = 0
        self.start_requested = False
        self.stop_requested = False

        # poll interval
        self.next_timer = SingleShotTimer(self.on_next_timeout, interval=200)

    @Slot(Terminal)
    def set_terminal(self, terminal: Terminal):
        self.terminal = terminal
        self.terminal.reply.connect(self.on_reply)

    def get_next_time(self) -> float:
        return self.points[-1].time + self.interval / binary_second if self.points else 0.0

    @Slot()
    def start(self, interval: int = 1000):
        if self.start_requested or self.started:
            logger.error("already started")
            return

        self.interval = interval  # ms
        self.time_offset = self.get_next_time()  # s
        print(self.time_offset)

        self.retries = 0
        self.start_requested = True
        self.stop_requested = False
        self.command(pack_uint32(b"v", interval))

    @Slot()
    def stop(self):
        if self.stop_requested or not self.started:
            logger.error("already stopped")
            return

        self.next_timer.stop()
        self.start_requested = False
        self.stop_requested = True
        self.command(STOP)

    @Slot()
    def reset(self):
        if self.started:
            return

        self.points = list()
        self.unsaved = 0
        self.file_name = None
        self.auto_save = False

    def next_command(self):
        if not self.busy_timer.isActive() and self.command_queue:
            command = self.command_queue.pop(0)
            self.terminal.write(command)
            self.busy_timer.start()

    @Slot()
    def on_busy_timeout(self):
        logger.error("no reply")
        if self.started:
            if not self.stop_requested:  # next failed
                # try again
                if self.retries == 2:
                    self.do_stop()
                else:
                    self.next_timer.start()
                    self.retries += 1
            else:  # stop failed
                self.do_stop()
        else:  # start failed
            pass

    def command(self, command: bytes):
        self.command_queue.append(command)
        self.next_command()

    def do_stop(self):
        # auto_save the last records regardless the limit
        if self.auto_save and self.unsaved:
            self.save()

        logger.info("stopped")
        self.start_requested = False
        self.started = False
        self.started_changed.emit(False)

    @Slot(bytes)
    def on_reply(self, reply: bytes):
        self.busy_timer.stop()

        if reply == START:
            logger.info("started")
            self.started = True
            self.started_changed.emit(True)
            self.next_timer.start()

        elif reply[1:2] == b"v" and (reply[4:8] == b" red" or reply[4:8] == b" blu"):
            self.retries = 0
            if len(reply) > 8:
                self.add_new_points(reply[8:])
            if not self.stop_requested:
                self.next_timer.start()

        elif reply == STOP:
            self.do_stop()

        elif reply == ERROR:
            # overflow in firmware
            logger.error("error reply; some points will be missing")
            # restart
            self.started = False
            self.start_requested = False
            self.start(self.interval)

        self.next_command()

    @Slot()
    def on_next_timeout(self):
        self.command(NEXT)

    def add_new_points(self, payload: bytes):
        # start = time.time()
        new_points = [
            VoltmeterPoint.parse(buffer, time_offset=self.time_offset)
            for buffer in batched(payload, 8)
        ]
        self.points.extend(new_points)

        self.unsaved += len(new_points) * self.interval
        if self.auto_save and self.unsaved >= 5000:
            self.save()

        self.new_points.emit(new_points)
        # logger.info(f"add_new_points {int((time.time() - start) * 1000000)} us")

    def set_file_name(self, file_name):
        self.file_name = file_name

    def save(self):
        file = QSaveFile(self.file_name)

        if not file.open(QIODevice.OpenModeFlag.WriteOnly):
            logger.error(OpenError(file.errorString()))
            return False

        def write(text):
            file.write(text.encode("ascii"))

        version = metadata.version("lenlab")
        write(f"Lenlab MSPM0 {version} Voltmeter-Daten\n")
        write("Zeit; Kanal_1; Kanal_2\n")
        for point in self.points:
            write(point.line())

        if not file.commit():
            logger.error(SaveError(file.errorString()))
            return False

        self.unsaved = 0
        return True

    def set_auto_save(self, state: bool):
        self.auto_save = state
        # auto_save the last records regardless the limit
        if self.unsaved:
            self.save()


class OpenError(Message):
    english = """Error opening file for saving: {0}"""
    german = """Fehler beim Öffnen der Datei fürs Speichern: {0}"""


class SaveError(Message):
    english = """Error when saving: {0}"""
    german = """Fehler beim Speichern: {0}"""
