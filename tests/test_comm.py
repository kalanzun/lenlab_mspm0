import numpy as np
import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.protocol import pack
from lenlab.memory import KB, check_memory, memory_28k


def read(port: QSerialPort, size: int, timeout: int = 300) -> bytes:
    while port.bytesAvailable() < size and port.waitForReadyRead(timeout):  # about 1 KB per event
        pass

    return port.read(size).data()


@pytest.fixture(scope="module")
def memory(port: QSerialPort) -> np.ndarray:
    port.write(pack(b"mi28K"))  # init 28K
    reply = read(port, 8)
    assert reply == pack(b"mi28K")

    return memory_28k()


def test_knock(firmware, port: QSerialPort):
    port.write(firmware.knock_packet)
    reply = read(port, 8)
    assert reply == firmware.knock_packet


# @pytest.mark.repeat(4000)  # 100 MB, 21 minutes
def test_28k(firmware, cleanup, port: QSerialPort, memory: np.ndarray):
    # 4 MBaud: about 120 invalid packets per 100 MB
    #     round trip time: 120 ms, net transfer rate 230 KB/s
    # 1 MBaud: about 2 invalid packets per 100 MB
    #     round trip time: 320 ms, net transfer rate 90 KB/s
    port.write(pack(b"mg28K"))  # get 28K
    reply = read(port, 28 * KB)
    check_memory(b"mg28K", memory, reply)
