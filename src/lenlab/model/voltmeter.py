import logging
import time
from dataclasses import dataclass
from importlib import metadata
from itertools import batched
from typing import Self

from PySide6.QtCore import QObject, Qt, Signal, Slot

from ..launchpad.protocol import pack, pack_uint32
from ..launchpad.terminal import Terminal
from ..message import Message
from ..singleshot import SingleShotTimer
from .lenlab import Lenlab

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

    def line(self) -> str:
        return f"{self.time:f}; {self.value1:f}; {self.value2:f}\n"


class Voltmeter(QObject):
    terminal: Terminal | None

    active: bool
    active_changed = Signal(bool)

    points: list[VoltmeterPoint]
    new_last_point = Signal(VoltmeterPoint)

    unsaved: bool

    auto_save: bool
    auto_save_changed = Signal(bool)

    error = Signal(Message)

    def __init__(self, lenlab: Lenlab):
        super().__init__()
        self.lenlab = lenlab
        self.terminal = None

        self.active = False
        self.start_requested = False
        self.stop_requested = False
        self.interval = 1000
        self.time_offset = 0.0
        self.points = list()
        self.unsaved = False

        # auto save
        self.save_idx = 0
        self.file_name = None
        self.auto_save = False

        self.new_last_point.connect(
            lambda last_point: self.save(), Qt.ConnectionType.QueuedConnection
        )

        # no reply timeout
        self.busy_timer = SingleShotTimer(self.on_busy_timeout, interval=2000)
        self.command_queue = list()
        self.retries = 0

        # poll interval
        self.next_timer = SingleShotTimer(self.on_next_timeout, interval=200)

        # terminal
        self.lenlab.new_terminal.connect(self.on_new_terminal)

    @Slot(Terminal)
    def on_new_terminal(self, terminal: Terminal):
        self.terminal = terminal
        self.terminal.error.connect(self.on_terminal_error)
        self.terminal.reply.connect(self.on_reply)
        self.terminal.closed.connect(self.on_terminal_closed)

    @Slot(Message)
    def on_terminal_error(self, message: Message):
        self.terminal = None

        if self.active or self.start_requested:
            self.stopped()

    @Slot()
    def on_terminal_closed(self):
        self.terminal = None

        if self.active or self.start_requested:
            self.stopped()

    def stopped(self):
        logger.info("stopped")
        self.save(0)

        self.next_timer.stop()
        self.busy_timer.stop()
        self.start_requested = False
        if self.active:
            self.active = False
            self.active_changed.emit(False)

    def start(self, interval: int):
        if self.terminal is None:
            logger.error("start error: no terminal")
            return

        if self.active or self.start_requested:
            logger.error("start error: already started")
            return

        self.interval = interval  # ms
        self.restart()

    def restart(self):
        self.time_offset = (
            self.points[-1].time + self.interval / binary_second if self.points else 0.0
        )

        self.start_requested = True
        self.stop_requested = False
        self.command(pack_uint32(b"v", self.interval))

    @Slot()
    def stop(self):
        if self.terminal is None:
            logger.error("start error: no terminal")
            return

        if self.stop_requested or not self.active:
            logger.error("stop error: already stopped")
            return

        self.next_timer.stop()
        self.start_requested = False
        self.stop_requested = True

        try:
            self.command(STOP)
        except Exception as error:
            logger.error(error)

    def discard(self):
        self.save(0)

        self.save_idx = 0
        self.file_name = None

        if self.auto_save:
            self.auto_save = False
            self.auto_save_changed.emit(False)

        self.points = list()
        self.unsaved = False

    def command(self, command: bytes):
        self.command_queue.append(command)
        self.send_command()

    def send_command(self):
        if not self.busy_timer.isActive() and self.command_queue:
            if not self.terminal.is_open:
                logger.error("send command error: terminal not open")
                return

            self.busy_timer.start()
            command = self.command_queue.pop(0)
            self.terminal.write(command)

    @Slot(bytes)
    def on_reply(self, reply: bytes):
        self.busy_timer.stop()
        self.send_command()

        if reply == START:
            logger.info("started")
            self.active = True
            self.active_changed.emit(True)
            self.next_timer.start()

        elif reply[1:2] == b"v" and (reply[4:8] == b" red" or reply[4:8] == b" blu"):
            if len(reply) > 8:
                self.add_new_points(reply[8:])
            if not self.stop_requested:
                self.next_timer.start()

        elif reply == STOP:
            self.stopped()

        elif reply == ERROR:
            # reset or overflow in firmware
            self.error.emit(VoltmeterOverflowError())
            if not self.stop_requested:
                self.restart()

    @Slot()
    def on_busy_timeout(self):
        if self.active:
            if self.stop_requested:  # stop failed
                logger.error("stop timeout")
                self.stopped()
            else:  # next failed
                self.error.emit(VoltmeterNextTimeout())
                self.next_timer.start()  # retry
        else:  # start failed
            self.error.emit(VoltmeterStartTimeout())
            self.start_requested = False

    @Slot()
    def on_next_timeout(self):
        if self.active and not self.stop_requested:
            self.command(NEXT)

    def add_new_points(self, payload: bytes):
        new_points = [
            VoltmeterPoint.parse(buffer, time_offset=self.time_offset)
            for buffer in batched(payload, 8)
        ]

        self.points.extend(new_points)
        self.unsaved = True
        self.new_last_point.emit(new_points[-1])

    def save_as(self, file_name: str) -> bool:
        self.file_name = file_name

        try:
            start = time.time()

            with open(self.file_name, "w") as file:
                version = metadata.version("lenlab")
                # TODO: csv file format remove -Daten -> de and en
                file.write(f"Lenlab MSPM0 {version} Voltmeter-Daten\n")
                # TODO: csv file format translate?
                file.write("Zeit; Kanal_1; Kanal_2\n")
                for point in self.points:
                    file.write(point.line())

            # TODO: move here: self.file_name = file_name
            self.save_idx = len(self.points)
            self.unsaved = False

            logger.debug(
                f"save_as {len(self.points)} points {int((time.time() - start) * 1000)} ms"
            )
            return True

        except Exception as error:
            logger.error(f"error in save_as: {error}")
            self.error.emit(VoltmeterSaveError(error))

            if self.auto_save:
                self.auto_save = False
                self.auto_save_changed.emit(False)

            return False

    @Slot()
    def save(self, interval: int = 5000):
        if not self.auto_save:
            return

        n = interval // self.interval
        if self.save_idx + n > len(self.points):
            return

        try:
            start = time.time()
            with open(self.file_name, "a") as file:
                for point in self.points[self.save_idx :]:
                    file.write(point.line())

            self.save_idx = len(self.points)
            self.unsaved = False

            logger.debug(f"save {len(self.points)} points {int((time.time() - start) * 1000)} ms")

        except Exception as error:
            logger.error(f"error in save: {error}")
            self.error.emit(VoltmeterSaveError(error))

            self.auto_save = False
            self.auto_save_changed.emit(False)

    @Slot(bool)
    def set_auto_save(self, auto_save: bool):
        logger.info(f"set_auto_save {auto_save}")
        self.auto_save = auto_save
        self.save(0)


class VoltmeterOverflowError(Message):
    english = """The computer didn't read all values from the Launchpad in time.
    Some points are be missing."""
    german = """Der Computer hat nicht rechtzeitig alle Werte vom Launchpad gelesen.
    Manche Punkte fehlen."""


class VoltmeterStartTimeout(Message):
    english = """The Launchpad did not reply."""
    german = """Das Launchpad antwortet nicht."""


class VoltmeterNextTimeout(Message):
    english = """The Launchpad did not reply. Some points may be missing."""
    german = """Das Launchpad antwortet nicht. Manche Punkte könnten fehlen."""


class VoltmeterSaveError(Message):
    english = """Error saving the data:\n\n{0}"""
    german = """Fehler beim Speichern der Daten:\n\n{0}"""
