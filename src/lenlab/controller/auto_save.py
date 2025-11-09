from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from lenlab.controller.csv import CSVWriter
from lenlab.model.points import Points


class Flag(QObject):
    changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.value = False

    def __bool__(self) -> bool:
        return self.value

    @Slot(bool)
    def set(self, value):
        if value != self.value:
            self.value = value
            self.changed.emit(value)


class PathProperty(QObject):
    changed = Signal(str)

    value: Path | None

    def __init__(self):
        super().__init__()
        self.value = None

    def __bool__(self) -> bool:
        return self.value is not None

    def __str__(self) -> str:
        return self.value.name if self.value is not None else ""

    def set(self, value: Path | None):
        if value != self.value:
            self.value = value
            self.changed.emit(str(self))


class AutoSave(QObject):
    points: Points
    save_idx: int

    def __init__(self):
        super().__init__()
        self.points = Points()
        self.save_idx = 0

        self.auto_save = Flag()
        self.auto_save.changed.connect(self.on_auto_save_changed)

        self.file_path = PathProperty()

    def clear(self):
        self.points.clear()
        self.save_idx = 0

        self.auto_save.set(False)
        self.file_path.set(None)

    @Slot(bool)
    def on_auto_save_changed(self, auto_save: bool):
        if auto_save:
            self.save(buffered=False)

    csv_writer = CSVWriter("voltmeter")

    def save_as(self, file_path: Path):
        points = self.points

        with file_path.open("w") as file:
            self.csv_writer.write_head(file)
            self.csv_writer.write_data(
                file,
                points.get_time(self.save_idx),
                points.get_values(0),
                points.get_values(1),
            )

        points.unsaved = False
        self.save_idx = points.index
        self.file_path.set(file_path)

    def save(self, buffered: bool = True):
        points = self.points

        if not points.unsaved or not self.auto_save or not self.file_path:
            return

        if buffered:
            n = int(5.0 / points.interval)
            if points.index < self.save_idx + n:
                return

        with self.file_path.value.open("a") as file:
            self.csv_writer.write_data(
                file,
                points.get_time(self.save_idx),
                points.get_values(0, self.save_idx),
                points.get_values(1, self.save_idx),
            )

        points.unsaved = False
        self.save_idx = points.index
