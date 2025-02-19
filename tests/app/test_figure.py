import pytest
from PySide6.QtCore import QBuffer
from PySide6.QtSvg import QSvgGenerator

from lenlab.app.figure import LaunchpadFigure, PinAssignmentFigure


@pytest.fixture()
def render(qt_widgets, output):
    def render(widget, file_name=None):
        buffer = QBuffer()
        generator = QSvgGenerator()
        generator.setOutputDevice(buffer)
        generator.setSize(widget.sizeHint())

        widget.render(generator)
        data = buffer.data()
        assert data.size() > 100

        if file_name:
            file_path = output / file_name
            file_path.write_bytes(data.data())

    return render


def test_launchpad_figure(render):
    figure = LaunchpadFigure()
    render(figure, "launchpad_figure.svg")


def test_pin_assignment_figure(render):
    figure = PinAssignmentFigure()
    render(figure, "pin_assignment_figure.svg")
