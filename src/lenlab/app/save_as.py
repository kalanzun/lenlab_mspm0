from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from ..translate import tr


class SaveAs(QFileDialog):
    on_save_as: Callable | None = None
    on_success: Callable | None = None

    default_file_name: str | None = None

    def set_default_file_name(self, default_file_name: str):
        self.default_file_name = default_file_name
        self.selectFile(default_file_name)
        self.setDefaultSuffix(default_file_name.split(".")[-1])

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # self.setModal(True)
        # setModal(True) and show() does not work on Mac (the dialog stays invisible)
        # calling open() instead of show() works fine on Mac, Linux, and Windows
        self.setFileMode(QFileDialog.FileMode.AnyFile)
        self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        self.fileSelected.connect(self.on_file_selected)

    @Slot(str)
    def on_file_selected(self, file_name):
        if self.on_save_as is not None:
            file_path = Path(file_name)
            self.on_save_as(file_path)

        if self.on_success is not None:
            self.on_success()


class UnsavedData(QMessageBox):
    on_cancel: Callable | None = None
    on_save: Callable | None = None
    on_discard: Callable | None = None

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setModal(True)
        self.setIcon(QMessageBox.Icon.Question)
        self.setStandardButtons(
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Save
        )
        self.addButton(tr("Discard", "Verwerfen"), QMessageBox.ButtonRole.DestructiveRole)
        self.finished.connect(self.on_finished)

    @Slot(int)
    def on_finished(self, result: int):
        if result == QMessageBox.StandardButton.Cancel:
            if self.on_cancel is not None:
                self.on_cancel()
        elif result == QMessageBox.StandardButton.Save:
            if self.on_save is not None:
                self.on_save()
        else:  # discard
            if self.on_discard is not None:
                self.on_discard()
