import time

from PySide6.QtCore import QCoreApplication, QIODevice, QTimer
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo


def main():
    """ModemManager blocks the device for 30 seconds.
    Either open fails or replies do not return sometimes."""
    app = QCoreApplication()

    start_time = time.time()

    match = QSerialPortInfo("ttyACM0")

    timer = QTimer()
    timer.count = 0
    timer.setSingleShot(True)
    timer.setInterval(100)

    def on_timeout():
        port = QSerialPort(match)

        print("open")
        if not port.open(QIODevice.OpenModeFlag.ReadWrite):
            print(port.errorString())
            timer.start()
            return

        port.setBaudRate(1_000_000)
        port.clear()  # windows might have leftovers

        def on_reply_timeout():
            print("reply timeout")
            port.close()
            timer.start()

        reply_timer = QTimer()
        reply_timer.setSingleShot(True)
        reply_timer.setInterval(100)
        reply_timer.timeout.connect(on_reply_timeout)

        def on_error_occurred():
            print(port.errorString())
            timer.start()

        port.errorOccurred.connect(on_error_occurred)

        def on_ready_read():
            reply_timer.stop()
            print("on ready read")
            print(port.read(8).data())
            timer.count += 1
            if timer.count == 100:
                port.close()
                app.quit()
            else:
                print("knock")
                reply_timer.start()
                port.write(b"Lk\x00\x00nock")

        port.readyRead.connect(on_ready_read)

        print("knock")
        reply_timer.start()
        port.write(b"Lk\x00\x00nock")

    timer.timeout.connect(on_timeout)
    timer.start()

    app.exec()

    runtime = round(time.time() - start_time, 2)
    print(f"{runtime=} seconds")


if __name__ == "__main__":
    main()


"""
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read

b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
Die Ressource ist zur Zeit nicht verfügbar
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
reply timeout
open
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
knock
on ready read
b'Lk\x00\x00nock'
runtime=38.3 seconds
"""
