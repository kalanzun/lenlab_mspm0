import numpy as np

from ..launchpad.protocol import pack

channel_length = 8 * 864
window = 6000


def example_reply(code: bytes = b"a") -> bytes:
    sampling_interval_25ns = 40  # 1 MHz
    # sine_samples = 4000  # 250 kHz
    offset = 88

    arg = sampling_interval_25ns.to_bytes(2, "little") + offset.to_bytes(2, "little")
    channel_1 = channel_2 = np.linspace(
        0, channel_length, channel_length, dtype=np.dtype("<u2")
    ).tobytes()

    return pack(code, arg, 2 * channel_length) + channel_1 + channel_2
