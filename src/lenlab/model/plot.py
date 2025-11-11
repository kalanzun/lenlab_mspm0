import numpy as np
from attrs import define


@define
class Plot:
    def get_plot_time_unit(self) -> float:
        raise NotImplementedError()

    def get_plot_time_range(self) -> tuple[float, float]:
        raise NotImplementedError()

    def get_plot_time(self, time_unit: float) -> np.ndarray:
        raise NotImplementedError()

    def get_plot_values(self, channel: int) -> np.ndarray:
        raise NotImplementedError()
