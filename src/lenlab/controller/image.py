from itertools import count
from pathlib import Path

from matplotlib import pyplot as plt

from ..model.chart import Chart


def save_image(file_path: Path, chart: Chart, channel_enabled: list[bool]):
    fig, ax = plt.subplots(figsize=[12.8, 9.6], dpi=150)

    ax.set_xlim(*chart.x_range)
    ax.set_ylim(*chart.y_range)

    ax.set_xlabel(chart.get_x_label())
    ax.set_ylabel(chart.get_y_label())

    ax.grid()

    if chart.channels is not None:
        iterator = zip(
            chart.channel_labels, chart.channels, channel_enabled, count(), strict=False
        )
        for label, values, enabled, i in iterator:
            if enabled:
                ax.plot(
                    chart.x,
                    values,
                    f"C{i}",  # index in the color cycle
                    label=label,
                )

        if any(channel_enabled):
            ax.legend()

    fig.savefig(file_path)
