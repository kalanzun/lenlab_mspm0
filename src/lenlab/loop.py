from enum import IntEnum

from PySide6.QtCore import QEventLoop

from lenlab.singleshot import SingleShotTimer


class ReturnCode(IntEnum):
    TIMEOUT = 0
    EVENT = 1
    KEYBOARD_INTERRUPT = 2


def loop_until(*signals, timeout=100) -> ReturnCode:
    # true: signal received
    # false: timeout
    loop = QEventLoop()
    connections = [signal.connect(lambda: loop.exit(ReturnCode.EVENT)) for signal in signals]
    timer = SingleShotTimer(lambda: loop.exit(ReturnCode.TIMEOUT), timeout)

    timer.start()
    return_code = ReturnCode(loop.exec())
    timer.stop()
    for signal, connection in zip(signals, connections, strict=True):
        signal.disconnect(connection)

    if return_code == ReturnCode.KEYBOARD_INTERRUPT:
        raise KeyboardInterrupt()

    return return_code
