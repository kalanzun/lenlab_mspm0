from importlib import metadata
from typing import TextIO

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

    def get_last_value(self, channel: int) -> float:
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

    def get_time(self, unit: float = 1.0, compression: bool = False) -> np.ndarray:
        batch_size = self.get_batch_size() if compression else 1
        return np.linspace(
            0.0,
            self.index * self.interval / unit,
            self.index // batch_size,
            endpoint=False,
            dtype=np.double,
        )

    def get_values(self, channel: int, compression: bool = False) -> np.ndarray:
        batch_size = self.get_batch_size()
        values = self.values[channel][: self.index]

        if compression and batch_size > 1:
            length = self.index // batch_size
            values = values[: length * batch_size].reshape((length, batch_size))
            values = values.mean(axis=1)

        return values

    def save_as(self, file: TextIO):
        version = metadata.version("lenlab")
        file.write(f"Lenlab MSPM0 {version} Voltmeter\n")
        file.write("Zeit; Kanal_1; Kanal_2\n")
        for t, ch1, ch2 in zip(
            self.get_time(), self.get_values(0), self.get_values(1), strict=True
        ):
            file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")
