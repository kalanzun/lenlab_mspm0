import numpy as np
from attrs import Factory, define


@define
class Points:
    seconds: np.ndarray = Factory(lambda: np.empty((6000,)))
    channels: tuple[np.ndarray, np.ndarray] = Factory(
        lambda: (np.empty((6000,)), np.empty((6000,)))
    )

    length: int = 6000
    index: int = 0

    def parse_reply(self, reply: bytes):
        interval_25ns = int.from_bytes(reply[4:8], byteorder="little")
        payload = np.frombuffer(reply, np.dtype("<u2"), offset=8)

        # 12 bit unsigned integer
        data = payload.astype(np.float64) / 4096 * 3.3  # 12 bit ADC
        length = data.shape[0] // 2  # 2 channels

        if self.index + length > self.length:
            self.length += 6000

            seconds = self.seconds
            self.seconds = np.empty((self.length,))
            self.seconds[: self.index] = seconds[: self.index]

            channels = self.channels
            self.channels = (np.empty((self.length,)), np.empty((self.length,)))
            for i in range(len(self.channels)):
                self.channels[i][: self.index] = channels[i][: self.index]

        interval = interval_25ns / 40_000_000
        offset = self.seconds[self.index - 1] + interval if self.index else 0
        time = np.arange(length) * interval + offset

        index = self.index + length

        self.seconds[self.index : index] = time
        for i in range(len(self.channels)):
            self.channels[i][self.index : index] = data[i::2]

        self.index = index

    @staticmethod
    def get_batch_size(last_time: float, interval: int) -> int:
        if last_time <= 2.0 * 60.0:  # 2 minutes
            return 1  # all points
        elif last_time <= 2 * 60.0 * 60.0:  # 2 hours
            return 1000 // interval  # seconds
        else:
            return 1000 // interval * 60  # minutes

    def get_seconds(self):
        return self.seconds[: self.index]

    def get_current_seconds(self):
        return self.seconds[self.index - 1] if self.index else 0

    def get_channel(self, i: int):
        return self.channels[i][: self.index]
