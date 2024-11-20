import logging
from importlib import metadata
from itertools import batched

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


class Voltmeter(QObject):
    terminal: Terminal

    # rename to active?
    started_changed = Signal(bool)
    new_records = Signal(list)

    def __init__(self):
        super().__init__()
        self.interval = 0
        self.offset = 0.0
        self.records = list()

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

    @Slot()
    def start(self, interval: int = 1000):
        if self.start_requested or self.started:
            logger.error("already started")
            return

        self.interval = interval  # ms
        if self.records:
            self.offset = self.records[-1][0] + interval / 1000.0  # s
        else:
            self.offset = 0.0

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

        del self.records[:]
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
                self.add_new_records(reply[8:])
            if not self.stop_requested:
                self.next_timer.start()

        elif reply == STOP:
            self.do_stop()

        elif reply == ERROR:
            logger.error("error reply")
            if self.started:
                self.do_stop()

        self.next_command()

    @Slot()
    def on_next_timeout(self):
        self.command(NEXT)

    def add_new_records(self, records: bytes):
        new_records = list()
        for record in batched(records, 8):
            time = int.from_bytes(record[:4], byteorder="little") / 1000.0 + self.offset
            value1 = int.from_bytes(record[4:6], byteorder="little") / 2**12 * 3.3
            value2 = int.from_bytes(record[6:8], byteorder="little") / 2**12 * 3.3
            new_records.append((time, value1, value2))

        self.records.extend(new_records)
        self.unsaved += len(new_records)
        self.do_auto_save()
        self.new_records.emit(new_records)

    def set_file_name(self, file_name):
        self.file_name = file_name

    def save(self):
        file = QSaveFile(self.file_name)

        if not file.open(QIODevice.OpenModeFlag.WriteOnly):
            logger.error(OpenError(file.errorString()))
            return False

        version = metadata.version("lenlab")
        file.write(f"Lenlab MSPM0 {version} Voltmeter-Daten\n".encode("ascii"))
        file.write("Zeit; Kanal_1; Kanal_2\n".encode("ascii"))
        for record in self.records:
            file.write(f"{record[0]:f}; {record[1]:f}; {record[2]:f}\n".encode("ascii"))

        if not file.commit():
            logger.error(SaveError(file.errorString()))
            return False

        self.unsaved = 0
        return True

    def set_auto_save(self, state: bool):
        self.auto_save = state
        self.do_auto_save()

    def do_auto_save(self):
        if self.auto_save and self.unsaved >= 5:
            self.save()


class OpenError(Message):
    english = """Error opening file for saving: {0}"""
    german = """Fehler beim Öffnen der Datei fürs Speichern: {0}"""


class SaveError(Message):
    english = """Error when saving: {0}"""
    german = """Fehler beim Speichern: {0}"""
