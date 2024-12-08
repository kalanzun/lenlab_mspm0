from xml.etree import ElementTree

from PySide6.QtCore import QBuffer, QRect, QSize
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgGenerator

from lenlab.app.box import Box
from lenlab.message import Message


def test_box_paint():
    generator = QSvgGenerator()

    painter = QPainter()

    generator.setSize(QSize(600, 200))
    generator.setViewBox(QRect(0, 0, generator.width(), generator.height()))

    buffer = QBuffer()
    generator.setOutputDevice(buffer)

    painter.begin(generator)
    Box.paint(painter)
    painter.end()

    svg = buffer.data().data()
    root = ElementTree.fromstring(svg)
    # an empty svg contains a single g without children
    assert len(root.findall("{*}g/*"))


def test_error():
    box = Box()
    box.set_error(Message(callback=lambda: None))
    box.on_clicked()
