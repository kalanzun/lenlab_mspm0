import logging
import sys
import time
from contextlib import closing

from ..launchpad.discovery import Discovery
from ..launchpad.protocol import check_memory_28k, make_memory_28k, pack
from ..loop import Loop
from ..spy import Spy

logger = logging.getLogger(__name__)


def profile(n=200):  # 64s
    discovery = Discovery()
    spy = Spy(discovery.result)
    discovery.error.connect(logger.error)
    discovery.discover()
    loop = Loop()
    loop.run_until(discovery.result, discovery.error, timeout=600)

    terminal = spy.get_single_arg()
    del discovery

    if terminal is None:
        logger.error("No firmware found")
        return

    logger.info(f"Firmware found on {terminal.port_name}")
    estimation = int(round(64 / 200 * n / 60))
    estimation = f"{estimation} minute{'' if estimation == 1 else 's'}"
    logger.info(f"Start profiling in {n} iterations. Estimated runtime {estimation}.")
    logger.info("You may cancel with Ctrl+C or Command+.")

    with closing(terminal):
        spy = Spy(terminal.reply)
        terminal.write(packet := pack(b"mi28K"))  # init 28K
        reply = spy.run_until_single_arg()
        assert reply == packet

        memory_28k = make_memory_28k()
        batch = 10 if n < 1000 else 100

        start = time.time()
        error_count = 0
        packet_times = []
        try:
            for i in range(n):
                try:
                    packet_start = time.time()

                    spy = Spy(terminal.reply)
                    terminal.write(pack(b"mg28K"))  # get 28K
                    reply = spy.run_until_single_arg()
                    assert reply is not None, "No reply"
                    check_memory_28k(reply, memory_28k)
                    # assert i % 7, "test error"
                    print(".", end="")
                    if (i + 1) % batch == 0:
                        print(f" [{int(round((i + 1)/n*100))}%]")
                    else:
                        sys.stdout.flush()  # print the dot right now

                    packet_time = int(round((time.time() - packet_start) * 1000))  # ms
                    packet_times.append(packet_time)
                except AssertionError as error:
                    error_count += 1
                    logger.error(error)
        except RuntimeError as error:
            logger.error(error)

    runtime = time.time() - start
    i += 1
    net_transfer_rate = int(round(28 * i / runtime))
    runtime = int(round(runtime))

    logger.info(f"{i=}")  # actual number of iterations
    logger.info(f"{error_count=}")
    logger.info(f"{runtime=}s")
    logger.info(f"{net_transfer_rate=}KB/s")

    packet_times.sort()
    median_packet_time = packet_times[len(packet_times) // 2]
    min_packet_time = packet_times[0]
    max_packet_time = packet_times[-1]
    highest_percentile = packet_times[-len(packet_times) // 100]

    logger.info(f"{median_packet_time=}ms")
    logger.info(f"{min_packet_time=}ms")
    logger.info(f"{max_packet_time=}ms")
    logger.info(f"{highest_percentile=}ms")
