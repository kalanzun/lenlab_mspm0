from pathlib import Path

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from lenlab.app.save_as import SaveAs


@pytest.fixture()
def get_save_file_name(monkeypatch):
    def get_save_file_name(parent, title, default_file_name, file_formats):
        return default_file_name, file_formats

    monkeypatch.setattr(QFileDialog, "getSaveFileName", get_save_file_name)


@pytest.fixture()
def critical(monkeypatch):
    def critical(parent, title, text):
        pytest.fail("SaveAs should not create an error dialog box")

    monkeypatch.setattr(QMessageBox, "critical", critical)


def test_save_as_assert_passthrough(get_save_file_name, critical):
    @SaveAs(
        "Title",
        "default.filename",
        "Binary (*.bin)",
    )
    def write(parent, file_name, file_format):
        raise AssertionError()

    # The assertion error passes through SaveAs
    with pytest.raises(AssertionError):
        write(None)


def test_save_as(get_save_file_name, critical):
    self = object()

    @SaveAs(
        "Title",
        "default.filename",
        "Binary (*.bin)",
    )
    def write(parent: object, file_name: Path, file_format: str):
        assert parent is self
        assert file_name.name == "default.filename"
        assert file_format == "Binary (*.bin)"

    write(self)


def test_save_as_cancel(get_save_file_name, critical):
    @SaveAs(
        "Title",
        "",
        "",
    )
    def write(parent, file_name, file_format):
        pytest.fail("SaveAs should have canceled")

    write(None)
