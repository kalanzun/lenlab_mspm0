import xml.etree.ElementTree as ET

import pytest
from PySide6.QtCore import QBuffer, QRect
from PySide6.QtGui import QPalette
from PySide6.QtSvg import QSvgGenerator

from lenlab.app.figure import LaunchpadFigure, PinAssignmentFigure


@pytest.mark.parametrize("Painter", [LaunchpadFigure, PinAssignmentFigure])
def test_figure(Painter):
    generator = QSvgGenerator()

    painter = Painter(QPalette())

    generator.setSize(painter.size_hint)
    generator.setViewBox(QRect(0, 0, generator.width(), generator.height()))

    buffer = QBuffer()
    generator.setOutputDevice(buffer)

    painter.begin(generator)
    painter.paint()
    painter.end()

    svg = buffer.data().data()
    root = ET.fromstring(svg)
    # an empty svg contains a single g without children
    assert len(root.findall("{*}g/*"))
