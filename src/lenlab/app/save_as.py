from contextlib import contextmanager, suppress

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


class Skip(Exception):
    pass


@contextmanager
def skippable():
    with suppress(Skip):
        yield


@contextmanager
def save_as(
    parent: QWidget, title: str, default_file_name: str, file_formats: str, mode: str = "w"
):
    file_name, file_format = QFileDialog.getSaveFileName(
        parent,
        title,
        default_file_name,
        file_formats,
    )

    if not file_name:
        raise Skip()

    try:
        with open(file_name, mode) as file:
            yield file

    except Exception as e:
        QMessageBox.critical(parent, title, str(e))
