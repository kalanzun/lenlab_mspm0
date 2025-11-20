from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from ..model.points import Points


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

    def __init__(self):
        super().__init__()
        self.points = Points()

        self.auto_save = Flag()
        self.auto_save.changed.connect(self.on_auto_save_changed)

        self.file_path = PathProperty()

    def clear(self):
        self.points.clear()

        self.auto_save.set(False)
        self.file_path.set(None)

    @Slot(bool)
    def on_auto_save_changed(self, auto_save: bool):
        if auto_save:
            self.save_update(buffered=False)

    def save_as(self, file_path: Path):
        with file_path.open("w", encoding="utf-8", newline="\n") as file:
            self.points.save_as(file)

        self.file_path.set(file_path)

    def save_update(self, buffered: bool = True):
        if not self.auto_save or not self.file_path or not self.points.unsaved:
            return

        if buffered:
            n = int(5.0 / self.points.interval)
            if self.points.index < self.points.save_idx + n:
                return

        file_path: Path = self.file_path.value
        with file_path.open("a", encoding="utf-8", newline="\n") as file:
            self.points.save_update(file)
