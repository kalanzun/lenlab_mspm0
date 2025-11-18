from typing import TextIO

import numpy as np
from attrs import Factory, define

from ..controller.csv import CSVTemplate
from .chart import Chart


@define
class Points:
    interval: float = 0.0  # seconds

    # 100_000 doubles is 800 KiB and 2.7 hours at 100 ms
    # 1 million doubles is 8 MiB and 5.5 hours at 20 ms
    channels: list[np.ndarray] = Factory(
        lambda: [np.empty((100_000,), dtype=np.double) for _ in range(2)]
    )  # volt
    index: int = 0

    chart_updated: bool = True
    chart_batch_size: int = 1
    chart_n_points: int = 0

    unsaved: bool = False
    save_idx: int = 0

    def clear(self):
        self.interval = 0.0
        self.index = 0
        self.chart_updated = True
        self.chart_batch_size = 1
        self.chart_n_points = 0
        self.unsaved = False
        self.save_idx = 0

    @staticmethod
    def select_batch_size(n_points: int, interval: float) -> int:
        time = (n_points - 1) * interval
        if time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif time <= 2 * 60.0 * 60.0:  # 2 hours
            return max(int(1 / interval), 1)  # seconds
        else:
            return int(60 / interval)  # minutes

    def parse_reply(self, reply: bytes):
        # interval = int.from_bytes(reply[4:8], byteorder="little")
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)
        length = payload.shape[0] // 2
        if length == 0:
            return

        payload = payload.reshape((length, 2), copy=False)  # 2 channels interleaved

        index = self.index + length
        for i, channel in enumerate(self.channels):
            if index > channel.shape[0]:
                self.channels[i] = channel = np.pad(channel, (0, 10_000), mode="empty")

            channel[self.index : index] = payload[:, i] / 4095 * 3.3

        self.index = index
        self.unsaved = True

        self.chart_batch_size = self.select_batch_size(index, self.interval)
        chart_n_points = self.index // self.chart_batch_size
        self.chart_updated = chart_n_points != self.chart_n_points
        self.chart_n_points = chart_n_points

    @staticmethod
    def compress(values, n_points, batch_size):
        values = values[: n_points * batch_size].reshape((n_points, batch_size))
        values = values.mean(axis=1)
        return values

    @staticmethod
    def select_x_unit(time: float) -> float:
        if time <= 2.0 * 60.0:  # 2 minutes
            return 1.0  # seconds
        elif time <= 2 * 60.0 * 60.0:  # 2 hours
            return 60.0  # minutes
        else:
            return 3600.0  # hours

    @staticmethod
    def select_x_range(x: float) -> tuple[float, float]:
        limits = [3.0, 6.0, 12.0, 18.0, 30.0, 45.0, 60.0, 90.0, 120.0]
        for limit in limits:
            if x <= limit:
                return 0.0, limit

        return 0.0, limits[-1]

    def create_chart(self) -> Chart:
        interval = self.interval
        batch_size = self.chart_batch_size
        n_points = self.chart_n_points

        if n_points == 0:
            return Chart()

        if batch_size > 1:
            channels = [self.compress(values, n_points, batch_size) for values in self.channels]
        else:
            channels = [values[:n_points] for values in self.channels]

        x_unit = self.select_x_unit(self.index * interval)
        x = np.arange(0, n_points) * batch_size * interval / x_unit
        x_range = self.select_x_range(x[-1])

        return Chart(x=x, channels=channels, x_unit=x_unit, x_range=x_range)

    def get_last_time(self) -> float:
        # invalid when empty
        return (self.index - 1) * self.interval

    def get_last_value(self, channel: int) -> float:
        # invalid when empty
        return self.channels[channel][self.index - 1]

    def rows(self, offset: int = 0):
        # uncompressed, time in seconds
        return zip(
            np.arange(offset, self.index) * self.interval,
            self.channels[0][offset : self.index],
            self.channels[1][offset : self.index],
            strict=True,
        )

    csv_template = CSVTemplate("voltmeter")

    def save_as(self, file: TextIO):
        file.write(self.csv_template.head())

        if self.unsaved:
            self.csv_template.write_rows(file.write, self.rows())

            self.unsaved = False
            self.save_idx = self.index

    def save_update(self, file: TextIO):
        if not self.unsaved:
            return

        self.csv_template.write_rows(file.write, self.rows(self.save_idx))

        self.unsaved = False
        self.save_idx = self.index
