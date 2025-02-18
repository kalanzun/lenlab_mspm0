from importlib import metadata
from typing import Self, TextIO

import numpy as np
from attrs import frozen


@frozen
class Waveform:
    length: int = 0
    offset: int = 0
    time_step: float = 0.0
    channels: tuple[np.ndarray, np.ndarray] = (np.ndarray((0,)), np.ndarray((0,)))

    @classmethod
    def parse_reply(cls, reply: bytes) -> Self:
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)
        sampling_interval_25ns = int.from_bytes(reply[4:6], byteorder="little")
        offset = int.from_bytes(reply[6:8], byteorder="little")

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

    def save_as(self, file: TextIO):
        version = metadata.version("lenlab")
        file.write(f"Lenlab MSPM0 {version} Oszilloskop\n")
        file.write("Zeit; Kanal_1; Kanal_2\n")
        for t, ch1, ch2 in zip(
            self.time_aligned(), self.channel_aligned(0), self.channel_aligned(1), strict=True
        ):
            file.write(f"{t:f}; {ch1:f}; {ch2:f}\n")
