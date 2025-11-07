from importlib import metadata

from PySide6.QtCore import QObject, Signal, Slot

from lenlab.model.points import Points


class AutoSave(QObject):
    points: Points | None
    save_idx: int

    unsaved: bool
    unsaved_changed = Signal(bool)

    auto_save: bool
    auto_save_changed = Signal(bool)

    file_name: str
    file_name_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.points = None
        self.save_idx = 0

        self.unsaved = False
        self.auto_save = False
        self.file_name = ""

    def set_points(self, points: Points):
        self.points = points
        self.save_idx = 0

        self.set_unsaved(bool(points.index))
        self.set_auto_save(False)
        self.set_file_name("")

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
    def set_file_name(self, file_name: str):
        self.file_name = file_name
        self.file_name_changed.emit(file_name)

    @Slot(str)
    def save_as(self, file_name: str):
        points = self.points

        with open(file_name, "w") as file:
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
        self.set_file_name(file_name)

    def save(self, interval: float = 5.0):
        if not self.auto_save or not self.file_name or not self.unsaved:
            return

        points = self.points
        n = int(interval / points.interval)
        if points.index < self.save_idx + n:
            return

        with open(self.file_name, "a") as file:
            for t, ch1, ch2 in zip(
                points.get_time(self.save_idx),
                points.get_values(0, self.save_idx),
                points.get_values(1, self.save_idx),
                strict=True,
            ):
                file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")

        self.save_idx = points.index
        self.set_unsaved(False)
