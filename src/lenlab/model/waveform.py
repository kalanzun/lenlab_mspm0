from typing import Self

import numpy as np
from attrs import frozen


@frozen
class Waveform:
    length: int
    time_step_ms: float
    time_ms: np.ndarray
    channels: tuple[np.ndarray, np.ndarray]

    @classmethod
    def parse_reply(cls, reply: bytes) -> Self:
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)
        sampling_interval_25ns = int.from_bytes(reply[4:8], byteorder="little")
        time_step_ms = sampling_interval_25ns * 25e-6

        # 12 bit signed binary (2s complement), left aligned
        # payload = payload >> 4

        # 12 bit unsigned integer
        data = payload.astype(np.float64) / 4096 * 3.3 - 1.65  # 12 bit ADC
        length = data.shape[0] // 2  # 2 channels
        assert length == 6 * 1024
        channels = (data[:length], data[length:])

        # time in milliseconds
        half = length // 2
        time_ms = np.linspace(-half, half, length, endpoint=False) * time_step_ms

        return cls(length, time_step_ms, time_ms, channels)
