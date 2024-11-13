from PySide6.QtCore import QEventLoop

from lenlab.singleshot import SingleShotTimer


class Loop(QEventLoop):
    def run_until(self, *signals, timeout: int = 100) -> bool:
        connections = [signal.connect(lambda: self.exit(0)) for signal in signals]
        timer = SingleShotTimer(lambda: self.exit(1), timeout)

        timer.start()
        return_code = self.exec()

        timer.stop()
        for signal, connection in zip(signals, connections, strict=True):
            signal.disconnect(connection)

        return return_code == 0
