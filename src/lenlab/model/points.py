import numpy as np
from attrs import define, field


@define
class Points:
    interval: float

    index: int = 0
    channels: list[np.ndarray] = field()

    @channels.default
    def _channels_factory(self):
        return [
            np.empty((100_000,), dtype=np.double),
            np.empty((100_000,), dtype=np.double),
        ]

    def parse_reply(self, reply: bytes):
        # interval = int.from_bytes(reply[4:8], byteorder="little")
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)
        length = payload.shape[0] // 2
        payload = payload.reshape((length, 2), copy=False)  # 2 channels interleaved

        index = self.index + length
        for i, channel in enumerate(self.channels):
            if index > channel.shape[0]:
                self.channels[i] = channel = np.pad(channel, (0, 10_000), mode="empty")

            channel[self.index : index] = payload[:, i] / 4096 * 3.3

        self.index = index

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

    def get_plot_time(self, unit: float = 1.0) -> np.ndarray:
        batch_size = self.get_batch_size()
        return np.linspace(
            0.0,
            self.index * self.interval / unit,
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
