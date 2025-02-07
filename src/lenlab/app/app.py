from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from ..language import Language


class App(QApplication):
    def __init__(self):
        super().__init__()

        # Qt translations
        path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        translator = QTranslator(self)
        if translator.load(QLocale(), "qtbase", "_", path):
            self.installTranslator(translator)

        # Message translations
        if QLocale().language() == QLocale.Language.German:
            Language.language = "german"
