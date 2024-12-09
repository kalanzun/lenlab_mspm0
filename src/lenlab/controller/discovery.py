from logging import getLogger
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from ..message import Message
from ..vocabulary import Vocabulary as Vocab
from . import linux
from .launchpad import find_launchpad
from .protocol import get_app_version, pack, unpack_fw_version
from .terminal import Terminal

logger = getLogger(__name__)


class Discovery(QObject):
    error = Signal(Message)
    ready = Signal(Terminal)

    discover_later = Signal()

    def __init__(self):
        super().__init__()

        self.discover_later.connect(self.discover, Qt.ConnectionType.QueuedConnection)

        self.port_info = None
        self.terminal = None

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        # can be slow on Windows
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.on_timeout)

    @Slot()
    def discover(self):
        try:
            if linux.is_linux() and not linux.check_rules():
                raise NoRules(callback=self.install_rules)

            matches = find_launchpad(QSerialPortInfo.availablePorts())
            if not matches:
                raise NoLaunchpad(callback=self.discover)
            logger.info(f"matches {", ".join(port_info.portName() for port_info in matches)}")

            self.port_info = matches[0]
            logger.info(f"probe {self.port_info.portName()}")

            port_path = Path(self.port_info.systemLocation())
            if linux.is_linux() and not linux.check_permission(port_path):
                if not linux.check_group(port_path):
                    raise NoGroup(
                        port_path,
                        linux.get_user_name(),
                        linux.get_group(port_path),
                        callback=self.add_to_group,
                    )
                else:
                    raise NoPermission(port_path, linux.get_user_name(), callback=self.discover)

            self.terminal = Terminal(QSerialPort(self.port_info))
            self.terminal.reply.connect(self.on_reply)
            self.terminal.error.connect(self.on_error)

            # on_error handles the error case
            if self.terminal.open():
                logger.info("send version question")
                self.timer.start()
                self.terminal.set_baud_rate(1_000_000)
                self.terminal.write(pack(b"8ver?"))

        except Message as error:
            logger.info(error.short())
            self.error.emit(error)

    def install_rules(self):
        linux.install_rules()
        self.discover()

    def add_to_group(self):
        port_path = Path(self.port_info.systemLocation())
        linux.add_to_group(port_path)
        self.discover()

    def fail(self, error: Message):
        self.timer.stop()
        self.terminal.close()
        logger.info(error.short())
        self.error.emit(error)

    @Slot(bytes)
    def on_reply(self, reply: bytes) -> None:
        logger.info("reply received")
        fw_version = unpack_fw_version(reply)
        app_version = get_app_version()
        if fw_version == app_version:
            self.timer.stop()
            self.terminal.reply.disconnect(self.on_reply)
            self.terminal.error.disconnect(self.on_error)
            logger.info(f"ready {self.terminal.port_name}")
            self.ready.emit(self.terminal)
        else:
            self.fail(InvalidFirmwareVersion(fw_version, app_version, callback=self.discover))

    @Slot(Message)
    def on_error(self, error: Message) -> None:
        error.button = Vocab.retry
        error.callback = self.discover
        self.fail(error)

    @Slot()
    def on_timeout(self) -> None:
        self.fail(NoFirmware(callback=self.discover))


class NoRules(Message):
    english = """No Launchpad rules installed
    
    The Launchpad rules prevent a program called ModemManager
    to connect to the Launchpad and block Lenlab.
    
    Disconnect the Launchpad from the computer
    to cancel any current communication from ModemManager
    and install the Launchpad rules.

    "Install rules" asks for root access.
    """

    german = """Keine Launchpad-Regeln installiert
    
    Die Launchpad-Regeln verbieten einem Programms namens ModemManager
    den Verbindungsaufbau mit dem Launchpad und die Blockade Lenlabs.
    
    Trennen Sie das Launchpad vom Computer damit eine aktuelle Verbindung
    vom ModemManager unterbrochen wird und installieren Sie die Launchpad-Regeln. 
    
    "Regeln installieren" fragt nach root-Zugriff.
    """

    button = Vocab("Install rules", "Regeln installieren")


class NoLaunchpad(Message):
    english = """No Launchpad found
    
    Connect the Launchpad via USB to your computer."""

    german = """Kein Launchpad gefunden
    
    Verbinden Sie das Launchpad über USB mit Ihrem Computer."""

    button = Vocab.retry


class NoGroup(Message):
    english = """Permission denied on the Launchpad port {0}
    
    Your user "{1}" is not a member of the group "{2}".
    Add your user to the group.
    Restart your session (log out and back in) or restart the computer
    for the changes to take effect.

    "Add user to group" asks for root access.
    """

    german = """Zugriff verboten auf den Launchpad-Port {0}
    
    Ihr Benutzer "{1}" ist kein Mitglied der Gruppe "{2}".
    Fügen Sie Ihren Benutzer zur Gruppe hinzu.
    Melden Sie sich neu an oder starten Sie den Computer neu
    damit die Änderungen wirksam werden.

    "Benutzer zur Gruppe hinzufügen" fragt nach root-Zugriff.
    """

    button = Vocab("Add user to group", "Benutzer zur Gruppe hinzufügen")


class NoPermission(Message):
    english = """Permission denied on the Launchpad port {0}
    
    Your user "{1}" has not enough permission to access the Launchpad port.

    If you just added your user to the group,
    restart your session (log out and back in) or restart the computer
    for the changes to take effect.
    """

    german = """Zugriff verboten auf den Launchpad-Port {0}
    
    Ihr Benutzer "{1}" hat keine ausreichende Berechtigung.
    
    Falls Sie eben erst Ihren Benutzer zur Gruppe hinzugefügt haben,
    melden Sie sich neu an oder starten Sie den Computer neu
    damit die Änderungen wirksam werden.
    """

    button = Vocab.retry


class InvalidFirmwareVersion(Message):
    english = """Invalid firmware version: {0}

    This Lenlab requires version {1}.
    Write the current version to the Launchpad with the Programmer."""

    german = """Ungültige Firmware-Version: {0}

    Dieses Lenlab benötigt Version {1}.
    Schreiben Sie die aktuelle Version mit dem Programmierer auf das Launchpad."""

    button = Vocab.retry


class NoFirmware(Message):
    english = """No reply received from the Launchpad

    Lenlab requires the Lenlab firmware on the Launchpad.
    Write the firmware on the Launchpad with the Programmer.

    If the communication still does not work, you can try to reset the launchpad
    (push the RESET button), to switch off and on power to the launchpad (unplug USB connection
    and plug it back in), and to restart the computer."""

    german = """Keine Antwort vom Launchpad erhalten

    Lenlab benötigt die Lenlab-Firmware auf dem Launchpad.
    Schreiben Sie die Firmware mit dem Programmierer auf das Launchpad.

    Wenn die Kommunikation trotzdem nicht funktioniert können Sie das Launchpad neustarten
    (Taste RESET drücken), das Launchpad stromlos schalten (USB-Verbindung ausstecken
    und wieder anstecken) und den Computer neustarten."""

    button = Vocab.retry
