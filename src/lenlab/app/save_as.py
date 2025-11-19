from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QFileDialog, QWidget


class SaveAs(QFileDialog):
    save_as = Signal(Path)

    def __init__(self, parent: QWidget, title: str, default_file_name: str, on_save_as: Callable):
        super().__init__(parent)

        self.setModal(True)
        self.setFileMode(QFileDialog.FileMode.AnyFile)
        self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self.setWindowTitle(title)
        self.selectFile(default_file_name)
        self.setDefaultSuffix(default_file_name.split(".")[-1])
        self.fileSelected.connect(self.on_file_selected)

        self.save_as.connect(on_save_as)

    @Slot()
    def on_file_selected(self, file_name):
        self.save_as.emit(Path(file_name))
