import numpy as np
from attrs import define, field

from .plot import Plot


@define
class Points(Plot):
    interval: float = 0.0  # seconds

    channels: list[np.ndarray] = field()  # volt
    index: int = 0

    unsaved: bool = False

    @channels.default
    def _channels_factory(self):
        # 100_000 doubles is 800 KiB and 2.7 hours at 100 ms
        # 1 million doubles is 8 MiB and 5.5 hours at 20 ms
        return [np.empty((100_000,), dtype=np.double) for _ in range(2)]

    def clear(self):
        self.interval = 0.0
        self.index = 0
        self.unsaved = False

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

            channel[self.index : index] = payload[:, i] / 4096 * 3.3

        self.index = index
        self.unsaved = True

    def get_current_time(self) -> float:
        # invalid when empty
        return (self.index - 1) * self.interval

    def get_last_value(self, channel: int) -> float:
        # invalid when empty
        return self.channels[channel][self.index - 1]

    def get_batch_size(self) -> int:
        current_time = self.get_current_time()
        if current_time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif current_time <= 2 * 60.0 * 60.0:  # 2 hours
            return max(int(1 / self.interval), 1)  # seconds
        else:
            return int(60 / self.interval)  # minutes

    def get_plot_time_unit(self) -> float:
        current_time = self.get_current_time()
        if current_time <= 2.0 * 60.0:  # 2 minutes
            return 1.0  # seconds
        elif current_time <= 2 * 60.0 * 60.0:  # 2 hours
            return 60.0  # minutes
        else:
            return 3600.0  # hours

    def get_plot_time_range(self) -> tuple[float, float]:
        current_time = self.get_current_time() / self.get_plot_time_unit()
        limits = [4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0, 40.0, 60.0, 80.0, 100.0, 120.0]
        for x in limits:
            if x >= current_time:
                return 0.0, x

        return 0.0, limits[-1]

    def get_plot_time(self, time_unit: float) -> np.ndarray:
        batch_size = self.get_batch_size()
        return np.linspace(
            0.0,
            self.index * self.interval / time_unit,
            self.index // batch_size,
            endpoint=False,
            dtype=np.double,
        )

    def get_plot_values(self, channel: int) -> np.ndarray:
        values = self.channels[channel][: self.index]

        batch_size = self.get_batch_size()
        if batch_size > 1:
            length = self.index // batch_size
            values = values[: length * batch_size].reshape((length, batch_size))
            values = values.mean(axis=1)

        return values

    def get_time(self, offset: int) -> np.ndarray:
        return np.linspace(
            offset * self.interval,
            self.index * self.interval,
            self.index - offset,
            endpoint=False,
            dtype=np.double,
        )

    def get_values(self, channel: int, offset: int = 0) -> np.ndarray:
        return self.channels[channel][offset : self.index]
