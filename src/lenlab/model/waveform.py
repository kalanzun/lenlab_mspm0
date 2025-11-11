from pathlib import Path
from typing import Self

import numpy as np
from attrs import Factory, frozen

from ..controller.csv import CSVWriter
from .plot import Plot


@frozen
class Waveform(Plot):
    length: int = 0
    offset: int = 0
    time_step: float = 0.0
    channels: tuple[np.ndarray, np.ndarray] = Factory(lambda: (np.ndarray((0,)), np.ndarray((0,))))

    plot_value_range = -2.0, 2.0

    @classmethod
    def parse_reply(cls, reply: bytes) -> Self:
        sampling_interval_25ns = int.from_bytes(reply[4:6], byteorder="little")
        offset = int.from_bytes(reply[6:8], byteorder="little")
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)

        time_step = sampling_interval_25ns * 25e-9

        # 12 bit signed binary (2s complement), left aligned
        # payload = payload >> 4

        # 12 bit unsigned integer
        data = payload.astype(np.float64) / 4096 * 3.3 - 1.65  # 12 bit ADC
        length = data.shape[0] // 2  # 2 channels
        channels = (data[:length], data[length:])

        return cls(length, offset, time_step, channels)

    def get_plot_time_unit(self) -> float:
        return 1e-3

    def get_plot_time_range(self) -> tuple[float, float]:
        # in ms
        return -3e3 * 1e3 * self.time_step, 3e3 * 1e3 * self.time_step

    def get_plot_time(self, time_unit: float) -> np.ndarray:
        return np.arange(-3000, 3001, dtype=np.double) * (self.time_step / time_unit)

    def get_plot_values(self, channel: int) -> np.ndarray:
        return self.channels[channel][self.offset : self.offset + 6001]

    csv_writer = CSVWriter("oscilloscope")

    def save_as(self, file_path: Path):
        with file_path.open("w") as file:
            write = file.write
            write(self.csv_writer.head())
            line_template = self.csv_writer.line_template()
            # time is always 6001 points, channels may be empty
            for t, ch1, ch2 in zip(
                self.get_plot_time(1.0),
                self.get_plot_values(0),
                self.get_plot_values(1),
                strict=False,
            ):
                write(line_template % (t, ch1, ch2))
