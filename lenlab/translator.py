from typing import Iterable, Protocol, runtime_checkable

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QTabWidget, QWidget


class Translation:
    def translate(self, table):
        pass


@runtime_checkable
class TextWidget(Protocol):
    def text(self) -> str:
        pass

    def setText(self, text: str) -> None:
        pass


class TextTranslation(Translation):
    widget_class = TextWidget

    def __init__(self, widget: TextWidget):
        self.widget = widget
        self.key = widget.text()

    def translate(self, table):
        self.widget.setText(table[self.key])


class TabTranslation(Translation):
    widget_class = QTabWidget

    def __init__(self, widget: QTabWidget):
        self.widget = widget
        self.keys = [widget.tabText(i) for i in range(widget.count())]

    def translate(self, table):
        for i, key in enumerate(self.keys):
            self.widget.setTabText(i, table[key])


def create_translations(widget: QWidget) -> Iterable[Translation]:
    for child in widget.findChildren(QWidget):
        if isinstance(child, TextWidget) and child.text():
            yield TextTranslation(child)

        elif isinstance(child, QTabWidget):
            yield TabTranslation(child)

        yield from create_translations(child)


class Translator:
    def __init__(self, widget: QWidget):
        self.translations = list(create_translations(widget))

    def translate(self):
        if QLocale().language() == QLocale.Language.German:
            for tr in self.translations:
                tr.translate(german)


german = {
    "Start": "Start",
    "Stop": "Stop",
    "Sample rate": "Abtastrate",
    "Cancel": "Abbrechen",
    "Retry": "Neuer Versuch",
    "Program": "Programmieren",
    "Channel 1": "Kanal 1",
    "Channel 2": "Kanal 2",
    "Programmer": "Programmierer",
    "Voltmeter": "Voltmeter",
    "Oscilloscope": "Oszilloskop",
    "Bode Plotter": "Bode Plotter",
    "Amplitude": "Amplitude",
}
