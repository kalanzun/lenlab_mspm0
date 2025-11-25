from matplotlib.colors import TABLEAU_COLORS
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from ..model.chart import Chart
from ..translate import Translate


class ChartWidget(QWidget):
    labels = (
        Translate("Channel 1 (ADC 0, PA 24)", "Kanal 1 (ADC 0, PA 24)"),
        Translate("Channel 2 (ADC 1, PA 17)", "Kanal 2 (ADC 1, PA 17)"),
    )

    colors = (
        TABLEAU_COLORS["tab:blue"],
        TABLEAU_COLORS["tab:orange"],
    )

    def __init__(self, template: Chart):
        super().__init__()

        self.template = template

        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart = self.chart_view.chart()
        # chart.setTheme(QChart.ChartTheme.ChartThemeLight)  # default, grid lines faint
        # chart.setTheme(QChart.ChartTheme.ChartThemeDark)  # odd gradient
        # chart.setTheme(QChart.ChartTheme.ChartThemeBlueNcs)  # grid lines faint
        self.chart.setTheme(
            QChart.ChartTheme.ChartThemeQt
        )  # light and dark green, stronger grid lines

        self.x_axis = QValueAxis()
        self.x_axis.setRange(template.x_range[0], template.x_range[1])
        self.x_axis.setTickCount(7)
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(template.get_x_label())
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(template.y_range[0], template.y_range[1])
        self.y_axis.setTickCount(5)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText(template.get_y_label())
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.channels = [QLineSeries() for _ in self.labels]
        for channel, label, color in zip(self.channels, self.labels, self.colors, strict=True):
            channel.setPen(QPen(QColor.fromString(color)))
            channel.setName(str(label))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(self.y_axis)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

    def draw(self, chart: Chart):
        # channel.replaceNp iterates over the raw c-array
        # and copies the values into a QList<QPointF>
        # It cannot read views with strides
        for channel, values in zip(self.channels, chart.channels, strict=True):
            channel.replaceNp(chart.x, values)

        self.x_axis.setRange(chart.x_range[0], chart.x_range[1])
        self.x_axis.setTitleText(chart.get_x_label())

    def clear(self):
        for channel in self.channels:
            channel.clear()

        self.x_axis.setRange(self.template.x_range[0], self.template.x_range[1])
        self.x_axis.setTitleText(self.template.get_x_label())
