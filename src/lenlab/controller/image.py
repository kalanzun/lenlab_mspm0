from pathlib import Path

from matplotlib import pyplot as plt

from ..model.chart import Chart


def save_image(chart: Chart, file_path: Path, file_format: str):
    fig, ax = plt.subplots(figsize=[12.8, 9.6], dpi=150)

    ax.set_xlim(*chart.x_range)
    ax.set_ylim(*chart.y_range)

    ax.set_xlabel(chart.get_x_label())
    ax.set_ylabel(chart.get_y_label())

    ax.grid()

    for label, values in zip(chart.channel_labels, chart.channels, strict=True):
        ax.plot(
            chart.x,
            values,
            label=label,
        )

    ax.legend()

    fig.savefig(file_path, format=file_format[:3].lower())
