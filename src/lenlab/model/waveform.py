from typing import Self, TextIO

import numpy as np
from attrs import frozen

from ..controller.csv import CSVTemplate
from .chart import Chart


@frozen
class WaveformChart(Chart):
    x_unit: float = 1e-3
    x_range: tuple[float, float] = -15, 15
    y_range: tuple[float, float] = -2.0, 2.0


@frozen
class Waveform:
    length: int = 0
    offset: int = 0
    time_step: float = 0.0
    channels: list[np.ndarray] | None = None

    @classmethod
    def parse_reply(cls, reply: bytes) -> Self:
        sampling_interval_25ns = int.from_bytes(reply[4:6], byteorder="little")
        offset = int.from_bytes(reply[6:8], byteorder="little")
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)

        time_step = sampling_interval_25ns * 25e-9

        # 12 bit signed binary (2s complement), left aligned
        # payload = payload >> 4

        # 12 bit unsigned integer
        data = payload.astype(np.float64) / 4095 * 3.3 - 1.65  # 12 bit ADC
        length = data.shape[0] // 2  # 2 channels
        channels = [data[:length], data[length:]]

        return cls(length, offset, time_step, channels)

    def create_chart(self) -> WaveformChart:
        n_points = 6001
        x_unit = 1e-3  # ms

        if self.channels is None:
            return WaveformChart()

        channels = [values[self.offset : self.offset + n_points] for values in self.channels]

        half = n_points // 2
        x = np.arange(-half, half + 1) * self.time_step / x_unit

        return WaveformChart(x=x, channels=channels, x_unit=x_unit, x_range=(x[0], x[-1]))

    csv_template = CSVTemplate("oscilloscope")

    def save_as(self, file: TextIO):
        file.write(self.csv_template.head())

        if self.length:
            chart = self.create_chart()
            self.csv_template.write_rows(file.write, chart.rows())
