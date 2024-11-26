import logging

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from ..message import Message
from ..singleshot import SingleShotTimer
from .launchpad import find_vid_pid
from .protocol import get_app_version, pack, unpack_fw_version
from .terminal import Terminal

logger = logging.getLogger(__name__)


class Probe(QObject):
    result = Signal(Terminal)
    error = Signal(Message)
    timeout = Signal()

    def __init__(self, terminal: Terminal):
        super().__init__()

        self.terminal = terminal
        self.unsuccessful = False
        self.timer = SingleShotTimer(self.on_timeout)

    def start(self) -> None:
        self.terminal.reply.connect(self.on_reply)
        self.terminal.error.connect(self.on_error)

        # on_error handles the error case
        if self.terminal.open():
            self.timer.start()
            self.terminal.set_baud_rate(1_000_000)
            self.terminal.write(pack(b"8ver?"))

    def fail(self, error: Message):
        self.timer.stop()
        self.terminal.close()
        self.unsuccessful = True
        self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        if fw_version := unpack_fw_version(reply):
            app_version = get_app_version()
            if fw_version == app_version:
                self.timer.stop()
                self.terminal.reply.disconnect(self.on_reply)
                self.terminal.error.disconnect(self.on_error)
                self.result.emit(self.terminal)
            else:
                self.fail(InvalidFirmwareVersion(fw_version, app_version))

        else:
            self.fail(UnexpectedReply(self.terminal.port_name, reply))

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        if self.unsuccessful:
            return

        self.fail(error)

    @Slot()
    def on_timeout(self) -> None:
        logger.info(f"probe timeout on {self.terminal.port_name}")
        self.terminal.close()
        self.unsuccessful = True
        self.timeout.emit()

    def cancel(self) -> None:
        if self.unsuccessful:
            return

        logger.info(f"probe cancelled on {self.terminal.port_name}")
        self.timer.stop()
        self.terminal.close()
        self.unsuccessful = True


class Discovery(QObject):
    result = Signal(Terminal)
    error = Signal(Message)

    probes: list[Probe]

    def __init__(self):
        super().__init__()

        self.comm_errors = list()

    def discover(self):
        port_infos = QSerialPortInfo.availablePorts()
        matches = find_vid_pid(port_infos)
        if not matches:
            self.error.emit(NoLaunchpad())
            return

        self.start([Probe(Terminal(QSerialPort(port_info))) for port_info in matches])

    def start(self, probes: list[Probe]) -> None:
        self.probes = probes

        for probe in self.probes:
            probe.result.connect(self.on_result)
            probe.error.connect(self.on_error)
            probe.timeout.connect(self.on_timeout)
            probe.start()

    @Slot(Terminal)
    def on_result(self, result: Terminal) -> None:
        self.result.emit(result)
        for probe in self.probes:
            if probe is not self.sender():
                probe.cancel()

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        if isinstance(error, InvalidFirmwareVersion | UnexpectedReply):
            # these cancel discovery
            self.error.emit(error)
            for probe in self.probes:
                if probe is not self.sender():
                    probe.cancel()
        else:
            # collect them and emit them if discovery fails
            self.comm_errors.append(error)
            self.on_timeout()

    @Slot()
    def on_timeout(self) -> None:
        if all(probe.unsuccessful for probe in self.probes):
            if not self.comm_errors:
                self.error.emit(NoFirmware())
            elif all(error == self.comm_errors[0] for error in self.comm_errors):
                # true for length 1
                self.error.emit(self.comm_errors[0])
            else:
                content = "\n\n".join(str(error) for error in self.comm_errors)
                self.error.emit(TerminalErrors(content))


class InvalidFirmwareVersion(Message):
    english = """### Invalid firmware version: {0}
    
    This Lenlab requires version {1}.
    Please write the current version to the Launchpad with the Programmer."""

    german = """### Ungültige Firmware-Version: {0}
    
    Dieses Lenlab benötigt Version {1}.
    Bitte die aktuelle Version mit dem Programmierer auf das Launchpad schreiben."""


class UnexpectedReply(Message):
    english = "Unexpected reply on {0}: {1}"
    german = "Unerwartete Antwort auf {0}: {1}"


class NoLaunchpad(Message):
    english = """### No Launchpad found
    
    Please connect the Launchpad via USB to the computer."""

    german = """### Kein Launchpad gefunden
    
    Bitte das Launchpad über USB mit dem Computer verbinden."""


class NoFirmware(Message):
    english = """### No reply from the Launchpad
    
    Lenlab requires the Lenlab firmware on the Launchpad.
    Please write the firmware on the Launchpad with the Programmer.
    
    If the communication still does not work, you can try to reset the launchpad
    (push the RESET button), to switch off power to the launchpad (unplug USB connection
    and plug it back in), and to restart the computer."""

    german = """### Keine Antwort vom Launchpad
    
    Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
    Bitte die Firmware mit dem Programmierer auf das Launchpad schreiben.
    
    Wenn die Kommunikation trotzdem nicht funktioniert können Sie das Launchpad neustarten
    (Taste RESET drücken), das Launchpad stromlos schalten (USB-Verbindung ausstecken
    und wieder anstecken) und den Computer neustarten."""


class TerminalErrors(Message):
    english = "{0}"
    german = "{0}"
