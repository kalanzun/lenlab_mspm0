from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QWidget


class SaveAs:
    @staticmethod
    def get_file_path(
        parent: QWidget | None, title: str, default_file_name: str, file_formats: list[str]
    ) -> tuple[Path | None, str | None]:
        file_name, file_format = QFileDialog.getSaveFileName(
            parent,
            title,
            default_file_name,
            ";;".join(file_formats),
        )

        if not file_name:  # the dialog was canceled
            return None, None

        file_path = Path(file_name)
        return file_path, file_format
