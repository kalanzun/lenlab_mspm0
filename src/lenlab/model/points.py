import numpy as np
from attrs import define, field


@define
class Points:
    interval: float

    index: int = 0
    values: list[np.ndarray] = field()

    @values.default
    def get_values_default(self):
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
        for i, values in enumerate(self.values):
            if index > values.shape[0]:
                self.values[i] = values = np.pad(values, (0, 10_000), mode="empty")

            values[self.index : index] = payload[:, i] / 4096 * 3.3

        self.index = index

    def get_current_time(self) -> float:
        # invalid when empty
        return (self.index - 1) * self.interval

    def get_last_values(self, channel: int) -> float:
        # invalid when empty
        return self.values[channel][self.index - 1]

    def get_batch_size(self) -> int:
        current_time = self.get_current_time()
        if current_time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif current_time <= 2 * 60.0 * 60.0:  # 2 hours
            return max(int(round(1 / self.interval)), 1)  # seconds
        else:
            return int(round(60 / self.interval))  # minutes

    def get_plot_time(self, unit: float = 1.0) -> np.ndarray:
        batch = self.get_batch_size()
        return np.linspace(
            0.0,
            self.index * self.interval / unit,
            self.index // batch,
            endpoint=False,
            dtype=np.double,
        )

    def get_plot_values(self, channel: int) -> np.ndarray:
        batch = self.get_batch_size()
        values = self.values[channel][: self.index]

        if batch > 1:
            length = self.index // batch
            values = values[: length * batch].reshape((length, batch))
            values = values.mean(axis=1)

        return values
