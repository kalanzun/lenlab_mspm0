from contextlib import contextmanager
from dataclasses import dataclass

from PySide6.QtCharts import QChart, QLineSeries
from PySide6.QtCore import QPoint, QPointF, QRect, QSize
from PySide6.QtGui import QColor, QPainter, QPen, Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from ..message import Message
from . import symbols
from .poster import PosterWidget

white = QColor(0xF0, 0xF0, 0xF0)
black = QColor(0x10, 0x10, 0x10)


@contextmanager
def save_and_restore(painter):
    painter.save()
    yield
    painter.restore()


def find_chart_colors(n=4):
    chart = QChart()
    chart.setTheme(QChart.ChartTheme.ChartThemeQt)  # light and dark green, stronger grid lines
    for _ in range(n):
        channel = QLineSeries()
        chart.addSeries(channel)
        yield channel.color()


class LaunchpadFigure(QWidget):
    def sizeHint(self):
        width = 96
        horizontal_scale = 4
        vertical_scale = 6
        return QSize(width * horizontal_scale, width * vertical_scale)

    def minimumSizeHint(self):
        size = self.sizeHint()
        return QSize(size.width() // 2, size.height() // 2)

    @staticmethod
    def draw_switch(painter: QPainter):
        # cut-out
        # on dark background, the black button has better contrast on the red board
        # painter.setBrush(self.background)
        # painter.drawRect(-4, 0, 8, 2)

        # button
        painter.setBrush(black)
        painter.drawRect(-2, 0, 4, 2)

        # body
        painter.setBrush(white)
        painter.drawRect(-4, 2, 8, 3)

    def draw_arrow(self, painter: QPainter):
        painter.translate(0, -2)
        painter.setBrush(self.palette().toolTipText())
        painter.drawPolygon(
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

    @staticmethod
    def draw_header(painter: QPainter):
        def pin_iter():
            for y in range(10):
                yield QPointF(0, 2.5 * y)
                yield QPointF(2.5, 2.5 * y)

        painter.setPen(QColor(0xA0, 0xA0, 0xA0))
        painter.drawPoints(list(pin_iter()))

    @staticmethod
    def draw_led(painter: QPainter, color: QColor):
        painter.setBrush(color)
        painter.drawRect(-1, -1, 2, 2)

        painter.setPen(color)
        for _ in range(6):
            painter.drawLine(3, 0, 5, 0)
            painter.rotate(60)

    def draw_board(self, painter: QPainter):
        painter.setPen(Qt.PenStyle.NoPen)

        # board
        painter.setBrush(QColor(0xCC, 0, 0))
        painter.drawRect(0, 0, 60, 108)

        # xds110
        painter.setBrush(black)
        painter.drawRect(11, 16, 15, 15)

        # controller
        painter.drawRect(28, 62, 10, 10)

        # usb plug
        painter.drawRect(7, -20, 10, 18)
        painter.drawRect(10, -32, 4, 12)

        # usb connector
        painter.setBrush(QColor(0x60, 0x60, 0x60))
        painter.drawRect(8, 0, 8, 5)
        painter.setBrush(QColor(0xA0, 0xA0, 0xA0))
        painter.drawRect(8, -2, 8, 2)

        # border
        with save_and_restore(painter):
            painter.translate(0, 41)
            painter.setPen(white)
            for i in range(20):
                painter.drawLine(1 + 3 * i, 0, 2 + 3 * i, 0)

        # holes
        with save_and_restore(painter):
            painter.setPen(QPen(self.palette().window(), 3, c=Qt.PenCapStyle.RoundCap))
            painter.drawPoint(2, 2)
            painter.drawPoint(60 - 2, 2)
            painter.drawPoint(2, 108 - 2)
            painter.drawPoint(60 - 2, 108 - 2)

        # switches
        with save_and_restore(painter):
            painter.translate(48, 0)
            self.draw_switch(painter)
            self.draw_arrow(painter)

        with save_and_restore(painter):
            painter.translate(0, 46)
            painter.rotate(-90)
            self.draw_switch(painter)
            self.draw_arrow(painter)

        with save_and_restore(painter):
            painter.translate(60, 46)
            painter.rotate(90)
            self.draw_switch(painter)

        # pin headers
        with save_and_restore(painter):
            painter.translate(7, 53)
            self.draw_header(painter)

        with save_and_restore(painter):
            painter.translate(60 - 7 - 2.5, 53)
            self.draw_header(painter)

        # pin arrow
        with save_and_restore(painter):
            painter.translate(7, 68)
            painter.rotate(-90)
            self.draw_arrow(painter)

        # green LED
        with save_and_restore(painter):
            painter.translate(3, 38)
            self.draw_led(painter, QColor(0, 0xFF, 0))

    @staticmethod
    def draw_label(painter: QPainter, x: int, y: int, text: str):
        width = painter.fontMetrics().horizontalAdvance(text)
        # height = painter.fontMetrics().height()
        painter.drawText(QPointF(x - width / 2, y), text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        sx = self.width() / 96
        sy = self.height() / 144
        s = max(min(sx, sy, 4), 2)
        painter.scale(s, s)

        # painter area (96, 144)
        # board size (60, 108)
        # margin 1
        painter.translate(34, 34)

        self.draw_board(painter)

        # text
        painter.scale(0.5, 0.5)
        painter.setPen(self.palette().toolTipText().color())
        self.draw_label(painter, 48 * 2, (-22 - 4) * 2, "Reset")
        self.draw_label(painter, -22 * 2, (46 - 6) * 2, "S1")
        self.draw_label(painter, (7 - 22) * 2, (68 - 6) * 2, "Pins")


@dataclass
class Pin:
    label: str
    fg: QColor
    bg: QColor
    name: str = ""


class PinAssignmentFigure(QWidget):
    unit = 32

    def __init__(self):
        super().__init__()

        channel_colors = list(find_chart_colors(4))

        self.pins = {
            1: Pin("3V3", white, QColor(0xC0, 0, 0)),
            21: Pin("5V", white, QColor(0xC0, 0, 0)),
            22: Pin("GND", white, black),
            27: Pin("ADC0", black, channel_colors[0], name="PA 24"),
            28: Pin("ADC1", black, channel_colors[1], name="PA 17"),
            30: Pin("DAC", black, channel_colors[2], name="PA 15"),
        }

    def sizeHint(self):
        return QSize(12 * self.unit, 12 * self.unit)

    def minimumSizeHint(self):
        return self.sizeHint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        font = painter.font()
        font.setPointSize(16)
        painter.setFont(font)

        painter.translate(4.5 * self.unit, 1.5 * self.unit)
        self.draw_pin_header(painter)

        painter.setPen(white)
        with save_and_restore(painter):
            self.draw_labels(painter)

        with save_and_restore(painter):
            painter.translate(self.unit, 0)
            self.draw_labels(painter, right=True)

    def draw_pin_header(self, painter: QPainter):
        painter.setPen(self.palette().toolTipText().color())
        margin = self.unit // 2
        painter.drawRect(-margin, -margin, self.unit + 2 * margin, 9 * self.unit + 2 * margin)

        painter.setPen(QPen(QColor(0xA0, 0xA0, 0xA0), 16))
        points = [QPoint(x * self.unit, y * self.unit) for x in range(2) for y in range(10)]
        painter.drawPoints(points)

    def draw_labels(self, painter: QPainter, right=False):
        for i in range(10):
            pin = self.pins.get(i + (21 if right else 1), None)
            if pin:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(pin.bg)

                rect = QRect(QPoint(0, 0), QSize(64, 24))
                rect.moveCenter(QPoint(56 if right else -56, 0))
                painter.drawRect(rect)

                painter.setPen(pin.fg)
                self.draw_text_center(painter, 56 if right else -56, 0, pin.label)

                if pin.name:
                    painter.setPen(self.palette().toolTipText().color())
                    self.draw_text_center(painter, 128 if right else -128, 0, str(pin.name))

            painter.translate(0, self.unit)

    @staticmethod
    def draw_text_center(painter: QPainter, x: int, y: int, text: str):
        rect = painter.fontMetrics().tightBoundingRect(text)
        rect.moveCenter(QPoint(x, y))
        # painter.drawRect(rect)
        painter.drawText(rect.bottomLeft(), text)


class LaunchpadWidget(QWidget):
    title = "Launchpad"

    def __init__(self):
        super().__init__()

        poster = PosterWidget()
        # do not call show before setLayout
        poster.set_message(MaximumPinVoltage())
        poster.set_symbol(symbols.dye(symbols.electric_bolt_48px, symbols.red))

        pins = PinAssignmentFigure()
        board = LaunchpadFigure()

        left = QVBoxLayout()
        left.addStretch()
        left.addWidget(poster)
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


class MaximumPinVoltage(Message):
    english = """Maximum pin voltage: 3.3 V

    Never directly connect a pin to 5 V or the solar cell.
    The voltage might damage the microcontroller.
    Use a voltage divider circuit."""

    german = """Maximalspannung an den Pins: 3.3 V

    Verbinden Sie einen Pin niemals direkt mit 5 V oder der Solarzelle.
    Die Spannung könnte den Mikrocontroller beschädigen.
    Verwenden Sie eine Spannungsteiler-Schaltung."""
