from logging import getLogger
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtSerialPort import QSerialPortInfo

from ..message import Message
from ..vocabulary import Vocabulary as Vocab
from . import linux
from .launchpad import find_launchpad

logger = getLogger(__name__)


class Discovery(QObject):
    error = Signal(Message)
    close = Signal()

    discover_later = Signal()

    def __init__(self):
        super().__init__()

        self.discover_later.connect(self.discover, Qt.ConnectionType.QueuedConnection)

        self.port_info = None
        self.port_path = None

    @Slot()
    def discover(self):
        try:
            if linux.is_linux() and not linux.check_rules():
                raise NoRules(callback=self.install_rules)

            matches = find_launchpad(QSerialPortInfo.availablePorts())
            if not matches:
                raise NoLaunchpad(callback=self.discover)

            self.port_info = matches[0]
            self.port_path = Path(self.port_info.systemLocation())

            if linux.is_linux() and not linux.check_permission(self.port_path):
                if not linux.check_group(self.port_path):
                    raise NoGroup(
                        self.port_path,
                        linux.get_user_name(),
                        linux.get_group(self.port_path),
                        callback=self.add_to_group,
                    )
                else:
                    raise NoPermission(
                        self.port_path,
                        linux.get_user_name(),
                        callback=self.close.emit,
                    )

        except Message as error:
            self.error.emit(error)

    def install_rules(self):
        linux.install_rules()
        self.discover()

    def add_to_group(self):
        linux.add_to_group(self.port_path)
        self.discover()


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

    button = Vocab("Close Lenlab", "Lenlab schließen")
