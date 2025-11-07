from importlib import metadata
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from lenlab.model.points import Points


class AutoSave(QObject):
    points: Points | None
    save_idx: int

    unsaved: bool
    unsaved_changed = Signal(bool)

    auto_save: bool
    auto_save_changed = Signal(bool)

    file_path: Path | None
    file_path_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.points = None
        self.save_idx = 0

        self.unsaved = False
        self.auto_save = False
        self.file_path = None

    def set_points(self, points: Points):
        self.points = points
        self.save_idx = 0

        self.set_unsaved(bool(points.index))
        self.set_auto_save(False)
        self.set_file_path(None)

    @Slot(bool)
    def set_unsaved(self, unsaved: bool):
        if unsaved != self.unsaved:
            self.unsaved = unsaved
            self.unsaved_changed.emit(unsaved)

    @Slot(bool)
    def set_auto_save(self, auto_save: bool):
        if auto_save != self.auto_save:
            self.auto_save = auto_save
            self.auto_save_changed.emit(auto_save)

            if auto_save:
                self.save(0)

    @Slot(bool)
    def set_file_path(self, file_path: Path | None):
        self.file_path = file_path
        self.file_path_changed.emit(file_path.name if file_path is not None else "")

    @Slot(str)
    def save_as(self, file_path: Path):
        points = self.points

        with file_path.open("w") as file:
            version = metadata.version("lenlab")
            file.write(f"Lenlab MSPM0 {version} Voltmeter\n")
            # TODO: csv file format translate?
            file.write("Zeit; Kanal_1; Kanal_2\n")
            for t, ch1, ch2 in zip(
                points.get_time(self.save_idx),
                points.get_values(0),
                points.get_values(1),
                strict=True,
            ):
                file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")

        self.save_idx = points.index
        self.set_unsaved(False)
        self.set_file_path(file_path)

    def save(self, interval: float = 5.0):
        if not self.unsaved or not self.auto_save or self.file_path is None:
            return

        points = self.points
        n = int(interval / points.interval)
        if points.index < self.save_idx + n:
            return

        with self.file_path.open("a") as file:
            for t, ch1, ch2 in zip(
                points.get_time(self.save_idx),
                points.get_values(0, self.save_idx),
                points.get_values(1, self.save_idx),
                strict=True,
            ):
                file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")

        self.save_idx = points.index
        self.set_unsaved(False)
