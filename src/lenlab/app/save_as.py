from collections.abc import Callable
from functools import wraps

from attrs import frozen
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


@frozen
class SaveAs:
    title: str
    default_file_name: str
    file_formats: str

    def __call__(self, method: Callable[[QWidget, str, str], None]) -> Callable[[QWidget], None]:
        @wraps(method)
        def wrapper(parent: QWidget):
            file_name, file_format = QFileDialog.getSaveFileName(
                parent,
                self.title,
                self.default_file_name,
                self.file_formats,
            )

            if not file_name:  # the dialog was canceled
                return

            try:
                method(parent, file_name, file_format)

            except AssertionError:  # pass through assertion errors for testing
                raise

            except Exception as e:  # display other errors
                QMessageBox.critical(parent, self.title, str(e))

        return wrapper
