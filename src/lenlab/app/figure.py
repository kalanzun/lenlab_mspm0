from contextlib import contextmanager
from dataclasses import dataclass

from PySide6.QtCharts import QChart, QLineSeries
from PySide6.QtCore import QPoint, QPointF, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPen, Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from lenlab.app.banner import MessageBanner
from lenlab.app.vocabulary import Vocabulary as Vocab
from lenlab.message import Message

white = QColor(0xF0, 0xF0, 0xF0)
black = QColor(0x10, 0x10, 0x10)


class Figure(QPainter):
    def __init__(self, palette):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        self.palette = palette

    @contextmanager
    def save_and_restore(self):
        self.save()
        yield
        self.restore()


def find_chart_colors(n=4):
    chart = QChart()
    chart.setTheme(QChart.ChartTheme.ChartThemeQt)  # light and dark green, stronger grid lines
    for _ in range(n):
        channel = QLineSeries()
        chart.addSeries(channel)
        yield channel.color()


class LaunchpadFigure(Figure):
    unit = 4
    size_hint = QSize(96 * unit, 144 * unit)

    def draw_switch(self):
        # cut-out
        # on dark background, the black button has better contrast on the red board
        # self.setBrush(self.background)
        # self.drawRect(-4, 0, 8, 2)

        # button
        self.setBrush(black)
        self.drawRect(-2, 0, 4, 2)

        # body
        self.setBrush(white)
        self.drawRect(-4, 2, 8, 3)

    def draw_arrow(self):
        self.translate(0, -2)
        self.setBrush(self.palette.toolTipText())
        self.drawPolygon(
            [
                QPoint(0, 0),
                QPoint(-5, -10),
                QPoint(-2, -10),
                QPoint(-2, -20),
                QPoint(2, -20),
                QPoint(2, -10),
                QPoint(5, -10),
            ]
        )

    def draw_header(self):
        def pin_iter():
            for y in range(10):
                yield QPointF(0, 2.5 * y)
                yield QPointF(2.5, 2.5 * y)

        self.setPen(QColor(0xA0, 0xA0, 0xA0))
        self.drawPoints(list(pin_iter()))

    def draw_led(self, color: QColor):
        self.setBrush(color)
        self.drawRect(-1, -1, 2, 2)

        self.setPen(color)
        for _ in range(6):
            self.drawLine(3, 0, 5, 0)
            self.rotate(60)

    def draw_board(self):
        self.setPen(Qt.PenStyle.NoPen)

        # board
        self.setBrush(QColor(0xCC, 0, 0))
        self.drawRect(0, 0, 60, 108)

        # xds110
        self.setBrush(black)
        self.drawRect(11, 16, 15, 15)

        # controller
        self.drawRect(28, 62, 10, 10)

        # usb plug
        self.drawRect(7, -20, 10, 18)
        self.drawRect(10, -32, 4, 12)

        # usb connector
        self.setBrush(QColor(0x60, 0x60, 0x60))
        self.drawRect(8, 0, 8, 5)
        self.setBrush(QColor(0xA0, 0xA0, 0xA0))
        self.drawRect(8, -2, 8, 2)

        # border
        with self.save_and_restore():
            self.translate(0, 41)
            self.setPen(white)
            for i in range(20):
                self.drawLine(1 + 3 * i, 0, 2 + 3 * i, 0)

        # holes
        with self.save_and_restore():
            self.setPen(QPen(self.palette.window(), 3, c=Qt.PenCapStyle.RoundCap))
            self.drawPoint(2, 2)
            self.drawPoint(60 - 2, 2)
            self.drawPoint(2, 108 - 2)
            self.drawPoint(60 - 2, 108 - 2)

        # switches
        with self.save_and_restore():
            self.translate(48, 0)
            self.draw_switch()
            self.draw_arrow()

        with self.save_and_restore():
            self.translate(0, 46)
            self.rotate(-90)
            self.draw_switch()
            self.draw_arrow()

        with self.save_and_restore():
            self.translate(60, 46)
            self.rotate(90)
            self.draw_switch()

        # pin headers
        with self.save_and_restore():
            self.translate(7, 53)
            self.draw_header()

        with self.save_and_restore():
            self.translate(60 - 7 - 2.5, 53)
            self.draw_header()

        # pin arrow
        with self.save_and_restore():
            self.translate(7, 68)
            self.rotate(-90)
            self.draw_arrow()

        # green LED
        with self.save_and_restore():
            self.translate(3, 38)
            self.draw_led(QColor(0, 0xFF, 0))

    def draw_label(self, x: int, y: int, text: str):
        width = self.fontMetrics().horizontalAdvance(text)
        # height = self.fontMetrics().height()
        self.drawText(QPointF(x - width / 2, y), text)

    def paint(self):
        # self area (96, 144)
        # board size (60, 108)
        # margin 1
        self.scale(self.unit, self.unit)
        self.translate(34, 34)

        self.draw_board()

        # text
        self.scale(0.5, 0.5)
        self.setPen(self.palette.toolTipText().color())
        self.draw_label(48 * 2, (-22 - 4) * 2, "Reset")
        self.draw_label(-22 * 2, (46 - 6) * 2, "S1")
        self.draw_label((7 - 22) * 2, (68 - 6) * 2, "Pins")


@dataclass
class Pin:
    label: str
    fg: QColor
    bg: QColor
    name: str = ""


class PinAssignmentFigure(Figure):
    unit = 32
    size_hint = QSize(12 * unit, 12 * unit)

    def paint(self):
        channel_colors = list(find_chart_colors(4))
        self.pins = {
            1: Pin("3V3", white, QColor(0xC0, 0, 0)),
            21: Pin("5V", white, QColor(0xC0, 0, 0)),
            22: Pin("GND", white, black),
            27: Pin("ADC0", black, channel_colors[0], name="PA 24"),
            28: Pin("ADC1", black, channel_colors[1], name="PA 17"),
            30: Pin("DAC", black, channel_colors[2], name="PA 15"),
        }

        font = self.font()
        font.setPointSize(16)
        self.setFont(font)

        self.translate(4.5 * self.unit, 1.5 * self.unit)
        self.draw_pin_header()

        self.setPen(white)
        with self.save_and_restore():
            self.draw_labels()

        with self.save_and_restore():
            self.translate(self.unit, 0)
            self.draw_labels(right=True)

    def draw_pin_header(self):
        self.setPen(self.palette.toolTipText().color())
        margin = self.unit // 2
        self.drawRect(-margin, -margin, self.unit + 2 * margin, 9 * self.unit + 2 * margin)

        self.setPen(QPen(QColor(0xA0, 0xA0, 0xA0), 16))
        points = [QPoint(x * self.unit, y * self.unit) for x in range(2) for y in range(10)]
        self.drawPoints(points)

    def draw_labels(self, right=False):
        for i in range(10):
            pin = self.pins.get(i + (21 if right else 1), None)
            if pin:
                self.setPen(Qt.PenStyle.NoPen)
                self.setBrush(pin.bg)

                rect = QRect(QPoint(0, 0), QSize(64, 24))
                rect.moveCenter(QPoint(56 if right else -56, 0))
                self.drawRect(rect)

                self.setPen(pin.fg)
                self.draw_text_center(56 if right else -56, 0, pin.label)

                if pin.name:
                    self.setPen(self.palette.toolTipText().color())
                    self.draw_text_center(128 if right else -128, 0, str(pin.name))

            self.translate(0, self.unit)

    def draw_text_center(self, x: int, y: int, text: str):
        rect = self.fontMetrics().tightBoundingRect(text)
        rect.moveCenter(QPoint(x, y))
        # painter.drawRect(rect)
        self.drawText(rect.bottomLeft(), text)


class PainterWidget(QWidget):
    def __init__(self, Painter):
        super().__init__()

        self.Painter = Painter

    def sizeHint(self):
        return self.Painter.size_hint

    def minimumSizeHint(self):
        return self.Painter.size_hint

    def paintEvent(self, event):
        painter = self.Painter(self.palette())
        painter.begin(self)
        painter.paint()
        painter.end()


class PinAssignmentWidget(QWidget):
    title = Vocab("Pin Assignment", "Pin-Belegung")

    def __init__(self):
        super().__init__()

        banner = MessageBanner()
        pins = PainterWidget(PinAssignmentFigure)
        board = PainterWidget(LaunchpadFigure)

        left = QVBoxLayout()
        left.addStretch()
        left.addWidget(banner)
        left.addWidget(pins, alignment=Qt.AlignmentFlag.AlignCenter)
        left.addStretch()

        right = QVBoxLayout()
        right.addStretch()
        right.addWidget(board)
        right.addStretch()

        layout = QHBoxLayout()
        layout.addStretch()
        layout.addLayout(left)
        layout.addLayout(right)
        layout.addStretch()

        self.setLayout(layout)
        # call show only after the layout is set
        banner.set_error(Voltage())  # calls show()


class Voltage(Message):
    english = """### Maximum pin voltage: 3.3 V
    
    Never directly connect a pin to the 5 V pin or the solar cell.
    Use a voltage divider circuit."""

    german = """### Maximalspannung an den Pins: 3.3 V
    
    Verbinden Sie einen Pin niemals direkt mit dem 5-V-Pin oder der Solarzelle.
    Verwenden Sie eine Spannungsteiler-Schaltung."""


def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication([])

    widget = PinAssignmentWidget()
    widget.show()

    app.exec()


if __name__ == "__main__":
    main()
