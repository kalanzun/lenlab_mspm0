import logging
import time
from contextlib import closing

from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo

from .discovery import Discovery, Probe
from .launchpad import find_vid_pid
from .loop import loop_until
from .memory import check_memory, memory_28k
from .protocol import pack
from .spy import Spy
from .terminal import Terminal

logger = logging.getLogger(__name__)


def profile():
    port_infos = QSerialPortInfo.availablePorts()
    matches = find_vid_pid(port_infos)
    if not matches:
        logger.error("no launchpad")
        return

    discovery = Discovery([Probe(Terminal(QSerialPort(port_info))) for port_info in matches])
    discovery.message.connect(logger.info)
    spy = Spy(discovery.result)
    discovery.start()
    no_timeout = loop_until(discovery.result, discovery.error, timeout=600)
    assert no_timeout, "at least one probe did neither emit an error nor the success signal"

    if not spy.count():
        logger.error("no firmware found")
        return

    terminal = spy.get_single_arg()
    logger.info(f"firmware found on {terminal.port_name}")

    with closing(terminal):
        spy = Spy(terminal.reply)
        terminal.write(pack(b"mi28K"))  # init 28K
        reply = spy.run_until_single_arg(timeout=600)
        assert reply == pack(b"mi28K")
        memory = memory_28k()

        # 64s
        n_iterations = 200
        batch_size = 20

        n_iterations = 10_000
        batch_size = 100

        start = time.time()
        error_count = 0
        for i in range(n_iterations):
            try:
                spy = Spy(terminal.reply)
                terminal.write(pack(b"mg28K"))  # get 28K
                reply = spy.run_until_single_arg(timeout=600)
                assert reply is not None, "reply timeout"
                check_memory(b"mg28K", memory, reply)
                # assert i % 7, "test error"
                print(".", end="")
                if (i + 1) % batch_size == 0:
                    print(f" [{int(round((i + 1)/n_iterations*100))}%]")
            except AssertionError as error:
                error_count += 1
                logger.error(error)

        runtime = time.time() - start
        net_transfer_rate = int(round(28 * n_iterations / runtime))
        runtime = int(round(runtime))
        logger.info(f"{n_iterations=}")
        logger.info(f"{error_count=}")
        logger.info(f"{runtime=}s")
        logger.info(f"{net_transfer_rate=}KB/s")
