from importlib import metadata, resources

from PySide6.QtWidgets import QFrame, QTextBrowser, QVBoxLayout, QWidget

import lenlab

from ..message import Message
from ..translate import Translate, tr


class About(QWidget):
    title = Translate("About", "Über")

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.message = QTextBrowser(self)
        self.message.setOpenExternalLinks(True)
        self.message.setFrameShape(QFrame.Shape.NoFrame)

        about = AboutMessage().long_form()
        file_path = resources.files(lenlab) / tr("datasheet.md", "datenblatt.md")
        datasheet = file_path.read_text(encoding="utf-8")
        self.message.setMarkdown(about + datasheet)

        layout.addWidget(self.message)

        self.setLayout(layout)


class AboutMessage(Message):
    english = f"""# Lenlab
    
    - Version: {metadata.version("lenlab")}
    - Homepage: https://github.com/kalanzun/lenlab_mspm0
    - Author: Christoph Simon
    
    ## Help
    
    In case of questions or problems, please contact your fellow students and tutors in ILIAS.
    
    When you don't find a solution there or when you've found an error in the software,
    please create an issue on the homepage on github.
    Describe the problem including the steps, which lead to the problem.
    Save the error report in the main menu (Lenlab -> Save error report)
    and attach the file.
    
    ## TI UniFlash Launchpad / LITO-board programmer
    
    TI offers a software package "UniFlash" to program Launchpads and LITO-boards:
     
    - Install https://www.ti.com/tool/UNIFLASH
    - Start Lenlab and export the firmware binary
      - Click on "Export firmware" in the Programmer
        and save the firmware binary
    - Start UniFlash. Select the exported firmware binary as "Flash Image"
    - Run "Load Image"
      - On success, it writes in the "Console":
        "\\[SUCCESS\\] Program Load completed successfully."
    - Restart Lenlab or click on "Retry"  
    """

    german = f"""# Lenlab
    
    - Version: {metadata.version("lenlab")}
    - Homepage: https://github.com/kalanzun/lenlab_mspm0
    - Autor: Christoph Simon
    
    ## Hilfe
    
    Bei Fragen oder Problemen wenden Sie sich bitte an Ihre Mitstudierenden und Betreuenden
    im ILIAS.
    
    Wenn Sie dort keine Lösung finden oder einen Fehler in der Software gefunden haben
    erstellen Sie bitte ein "issue" auf der Homepage auf Github.
    Beschreiben Sie das Problem einschließlich der Schritte, die zu dem Problem geführt haben.
    Speichern Sie bitte den Fehlerbericht im Hauptmenü (Lenlab -> Fehlerbericht speichern)
    und fügen Sie die Datei als Anlage hinzu.
    
    ## TI UniFlash Launchpad / LITO-Board Programmierer
    
    TI bietet ein Softwarepaket "UniFlash" an um Launchpads und LITO-Boards zu programmieren:
    
    - Installieren Sie https://www.ti.com/tool/UNIFLASH
    - Starten Sie Lenlab und exportieren Sie das Firmware-Binary
      - Klicken Sie im Programmierer auf "Firmware exportieren"
        und Speichern Sie das Firmware-Binary
    - Starten Sie UniFlash. Wählen Sie als "Flash Image" das exportierte Firmware-Binary
    - Führen Sie "Load Image" aus
      - Bei Erfolg schreibt es in die "Console":
        "\\[SUCCESS\\] Program Load completed successfully."
    - Starten Sie Lenlab neu oder klicken Sie auf "Neuer Versuch"
    """
