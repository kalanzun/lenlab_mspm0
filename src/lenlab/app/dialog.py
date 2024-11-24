from PySide6.QtWidgets import QMessageBox

from .vocabulary import Vocabulary as Vocab


class Dialog(QMessageBox):
    text: Vocab
    info: Vocab

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lenlab")
        self.setText(str(self.text))
        self.setInformativeText(str(self.info))
