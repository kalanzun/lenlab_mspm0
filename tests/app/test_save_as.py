import pytest
from PySide6.QtWidgets import QFileDialog

from lenlab.app.save_as import SaveAs


@pytest.fixture()
def get_save_file_name(monkeypatch):
    def get_save_file_name(parent, title, default_file_name, file_formats):
        return default_file_name, file_formats

    monkeypatch.setattr(QFileDialog, "getSaveFileName", get_save_file_name)


def test_save_as(get_save_file_name):
    file_path, file_format = SaveAs.get_file_path(
        None,
        "Title",
        "default.filename",
        ["Binary (*.bin)"],
    )

    assert file_path.name == "default.filename"
    assert file_format == "Binary (*.bin)"


def test_save_as_cancel(get_save_file_name):
    file_path, file_format = SaveAs.get_file_path(
        None,
        "Title",
        "",
        ["Binary (*.bin)"],
    )

    assert file_path is None
    assert file_format is None
