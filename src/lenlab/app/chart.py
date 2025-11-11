from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QHBoxLayout,
    QWidget,
)

from ..model.plot import Plot
from ..translate import Translate


class Chart(QWidget):
    labels = (
        Translate("Channel 1 (ADC 0, PA 24)", "Kanal 1 (ADC 0, PA 24)"),
        Translate("Channel 2 (ADC 1, PA 17)", "Kanal 2 (ADC 1, PA 17)"),
    )

    x_label = Translate("time [{0}]", "Zeit [{0}]")
    y_label = Translate("voltage [V]", "Spannung [V]")

    time_unit = 1.0
    time_labels = {
        1e-3: "ms",
        1.0: "s",
        60.0: "min",
        3600.0: "h",
    }

    x_range = (0.0, 4.0)
    y_range = (0.0, 4.0)

    x_tick_count = 5
    y_tick_count = 5

    def __init__(self):
        super().__init__()

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
        self.x_axis.setRange(self.x_range[0], self.x_range[1])
        self.x_axis.setTickCount(self.x_tick_count)
        self.x_axis.setLabelFormat("%g")
        self.x_axis.setTitleText(str(self.x_label).format(self.time_labels[self.time_unit]))
        self.chart.addAxis(self.x_axis, Qt.AlignmentFlag.AlignBottom)

        self.y_axis = QValueAxis()
        self.y_axis.setRange(self.y_range[0], self.y_range[1])
        self.y_axis.setTickCount(self.y_tick_count)
        self.y_axis.setLabelFormat("%g")
        self.y_axis.setTitleText(str(self.y_label))
        self.chart.addAxis(self.y_axis, Qt.AlignmentFlag.AlignLeft)

        self.channels = [QLineSeries() for _ in self.labels]
        for channel, label in zip(self.channels, self.labels, strict=True):
            channel.setName(str(label))
            self.chart.addSeries(channel)
            channel.attachAxis(self.x_axis)
            channel.attachAxis(self.y_axis)

        layout = QHBoxLayout()
        layout.addWidget(self.chart_view)
        self.setLayout(layout)

    def plot(self, plot: Plot):
        time_unit = plot.get_plot_time_unit()
        time = plot.get_plot_time(time_unit)

        # channel.replaceNp iterates over the raw c-array
        # and copies the values into a QList<QPointF>
        # It cannot read views or strides
        for i, channel in enumerate(self.channels):
            channel.replaceNp(time, plot.get_plot_values(i))

        time_range = plot.get_plot_time_range()
        self.x_axis.setRange(time_range[0], time_range[1])

        self.x_axis.setTitleText(str(self.x_label).format(self.time_labels[time_unit]))

    def clear(self):
        for channel in self.channels:
            channel.clear()

        self.x_axis.setRange(self.x_range[0], self.x_range[1])
        self.x_axis.setTitleText(str(self.x_label).format(self.time_labels[self.time_unit]))
