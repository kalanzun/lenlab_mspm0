from importlib import metadata, resources

from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

import lenlab

from ..message import Message
from ..translate import Translate, tr


class About(QWidget):
    title = Translate("About", "Über")

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.message = QTextBrowser(self)
        self.message.setOpenExternalLinks(True)

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
    """
