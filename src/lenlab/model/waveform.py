from typing import Self, TextIO

import numpy as np
from attrs import Factory, frozen

from lenlab.controller.csv import CSVWriter


@frozen
class Waveform:
    length: int = 0
    offset: int = 0
    time_step: float = 0.0
    channels: tuple[np.ndarray, np.ndarray] = Factory(lambda: (np.ndarray((0,)), np.ndarray((0,))))

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

    def time_aligned(self) -> np.ndarray:
        return np.linspace(-3e3, 3e3, 6001, endpoint=True) * self.time_step

    def channel_aligned(self, i: int) -> np.ndarray:
        return self.channels[i][self.offset : self.offset + 6001]

    csv_writer = CSVWriter("oscilloscope")

    def save_as(self, file: TextIO):
        # time is always 6001 points, channels may be empty
        self.csv_writer.write_head(file)
        self.csv_writer.write_data(
            file, self.time_aligned(), self.channel_aligned(0), self.channel_aligned(1)
        )
