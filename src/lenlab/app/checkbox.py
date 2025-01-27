from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QCheckBox


class BoolCheckBox(QCheckBox):
    check_changed = Signal(bool)

    def __init__(self, text):
        super().__init__()

        self.setText(str(text))
        self.checkStateChanged.connect(self.on_check_state_changed)

    @Slot(Qt.CheckState)
    def on_check_state_changed(self, state: Qt.CheckState):
        # bool(state) is always true
        self.check_changed.emit(state == Qt.CheckState.Checked)
