from PySide6.QtCore import QEventLoop, QTimer, SignalInstance


class Loop(QEventLoop):
    def run_until(self, *signals: SignalInstance, interval: int = 400) -> bool:
        connections = [signal.connect(lambda: self.exit(0)) for signal in signals]

        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(lambda: self.exit(1))
        timer.start()

        return_code = self.exec()
        if return_code == 130 or return_code == -1:  # -1: exec() failed
            raise RuntimeError("interrupted")

        timer.stop()
        for signal, connection in zip(signals, connections, strict=True):
            signal.disconnect(connection)

        return return_code == 0
