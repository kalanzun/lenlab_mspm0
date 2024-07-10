from contextlib import contextmanager

from PySide6.QtCore import QPoint, QPointF, QSize
from PySide6.QtGui import QColor, QPainter, QPen, Qt
from PySide6.QtWidgets import QApplication, QWidget

white = QColor(0xF0, 0xF0, 0xF0)
black = QColor(0x10, 0x10, 0x10)


@contextmanager
def save_and_restore(painter):
    painter.save()
    yield
    painter.restore()


class LaunchpadFigure(QWidget):
    def sizeHint(self):
        width = 96
        horizontal_scale = 4
        vertical_scale = 6
        return QSize(width * horizontal_scale, width * vertical_scale)

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


def main():
    app = QApplication([])

    figure = LaunchpadFigure()
    figure.show()

    app.exec()


if __name__ == "__main__":
    main()
