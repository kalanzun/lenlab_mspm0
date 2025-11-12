import numpy as np
from attrs import frozen

from ..translate import Translate


@frozen
class Chart:
    x: np.ndarray | None = None
    channels: list[np.ndarray] | None = None

    x_unit: float = 1.0
    x_range: tuple[float, float] = 0.0, 3.0
    y_range: tuple[float, float] = 0.0, 4.0

    channel_labels = (
        Translate("Channel 1", "Kanal 1"),
        Translate("Channel 2", "Kanal 2"),
    )

    x_label = Translate("time [{0}]", "Zeit [{0}]")
    y_label = Translate("voltage [V]", "Spannung [V]")

    unit_labels = {
        1e-3: "ms",
        1.0: "s",
        60.0: "min",
        3600.0: "h",
    }

    def get_x_label(self) -> str:
        return str(self.x_label).format(self.unit_labels[self.x_unit])

    def get_y_label(self) -> str:
        return str(self.y_label)

    def rows(self):
        return zip(self.x, *self.channels, strict=True)
