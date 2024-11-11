from PySide6.QtCore import QEventLoop

from lenlab.singleshot import SingleShotTimer


def loop_until(*signals, timeout=100) -> bool:
    # true: signal received
    # false: timeout
    loop = QEventLoop()
    connections = [signal.connect(lambda: loop.exit(0)) for signal in signals]
    timer = SingleShotTimer(lambda: loop.exit(1), timeout)

    timer.start()
    return_code = loop.exec()
    timer.stop()
    for signal, connection in zip(signals, connections, strict=True):
        signal.disconnect(connection)

    return not bool(return_code)
