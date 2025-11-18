from collections.abc import Callable
from functools import wraps
from pathlib import Path

from attrs import frozen
from PySide6.QtWidgets import QFileDialog, QWidget


@frozen
class SaveAs:
    title: str
    default_file_name: str
    file_formats: str

    def __call__(
        self, method: Callable[[QWidget, Path, str], None]
    ) -> Callable[[QWidget, Path | None, str], None]:
        @wraps(method)
        def wrapper(parent: QWidget, *, file_path: Path | None = None, file_format: str = ""):
            # * keyword-only arguments prevents Qt from setting an argument from a signal
            # The clicked signal of a push button comes with a checked=False argument
            if file_path is None:  # pass through for testing
                file_name, file_format = QFileDialog.getSaveFileName(
                    parent,
                    self.title,
                    self.default_file_name,
                    self.file_formats,
                )

                if not file_name:  # the dialog was canceled
                    return

                file_path = Path(file_name)

            method(parent, file_path, file_format)

        return wrapper
