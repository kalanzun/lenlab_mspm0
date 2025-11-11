from pathlib import Path

from matplotlib import pyplot as plt

from ..model.plot import Plot
from ..translate import Translate


labels = (
    Translate("Channel 1", "Kanal 1"),
    Translate("Channel 2", "Kanal 2"),
)

x_label = Translate("time [{0}]", "Zeit [{0}]")
y_label = Translate("voltage [V]", "Spannung [V]")

time_labels = {
    1e-3: "ms",
    1.0: "s",
    60.0: "min",
    3600.0: "h",
}


def save_image(plot: Plot, file_path: Path, file_format: str):
    fig, ax = plt.subplots(figsize=[12.8, 9.6], dpi=150)

    time_unit = plot.get_plot_time_unit()

    ax.set_xlim(*plot.get_plot_time_range())
    ax.set_ylim(0.0, 4.0)

    ax.set_xlabel(str(x_label).format(time_labels[time_unit]))
    ax.set_ylabel(str(y_label))

    ax.grid()

    time = plot.get_plot_time(time_unit)
    for i, label in enumerate(labels):
        ax.plot(
            time,
            plot.get_plot_values(i),
            label=label,
        )

    ax.legend()

    fig.savefig(file_path, format=file_format[:3].lower())
