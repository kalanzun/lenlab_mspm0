from pathlib import Path
from subprocess import run
from time import sleep

import pytest
from PySide6.QtSerialPort import QSerialPort

from lenlab.launchpad.bsl import pack

connect_packet = bytes((0x80, 0x01, 0x00, 0x12, 0x3A, 0x61, 0x44, 0xDE))
device_info = (
    b"\x00\x08\x19\x001\x00\x01\x00\x01\x00\x00\x00\x00\x01\x00"
    b"\xc0>`\x01\x00 \x01\x00\x00\x00\x01\x00\x00\x00\x0b_-\xd1"
)

ti_path = Path.home() / "ti"


@pytest.fixture
def ccs_path():
    paths = list(ti_path.glob("ccs*"))
    assert len(paths) == 1
    return paths[0]


@pytest.fixture
def dbg_jtag(ccs_path: Path):
    return ccs_path / "ccs/ccs_base/common/uscif/dbgjtag"


@pytest.fixture
def xds110_reset(ccs_path: Path):
    return ccs_path / "ccs/ccs_base/common/uscif/xds110/xds110reset"


def read_all(port, timeout: int = 100):
    reply = b""
    while port.waitForReadyRead(timeout):
        reply += port.readAll().data()
    return reply


@pytest.mark.parametrize("i", [(i,) for i in range(10)])
def test_bsl_connect(bsl, port: QSerialPort, xds110_reset: Path, i: int):
    # the boards boot into BSL when the pin PA 18 is high
    # it does not work during power-up, the voltage at the pin is not high quickly enough

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)

    # reset
    run([xds110_reset, "-d", "100"])
    sleep(0.2)  # 200 ms is minimum

    # connect packet
    port.write(connect_packet)
    print("reply", read_all(port))
    # LP-MSPM0G3507 always replies a single zero
    # MSP-LITO-G3507 replies anything, but rarely a single zero
    # Both do require the connect command

    port.write(pack(bytes([0x19])))  # device info
    reply = read_all(port)
    # print("device info", reply)
    assert reply == device_info

    # no leftover data
    # reply = read_all(port)
    # if reply:
    #     print("leftover", reply)
    # assert not reply


def _bsl_boot(bsl, port: QSerialPort, xds110_reset: Path, dbg_jtag: Path):
    # LP-MSPM0G3507 only
    run([dbg_jtag, "-f", "@xds110", "-Y", "gpiopins,config=0x1,write=0x1"])
    run([xds110_reset, "-d", "100"])
    sleep(0.2)

    # send the BSL connect packet at 9600 Baud
    port.setBaudRate(9_600)
    port.write(connect_packet)

    reply = read_all(port)
    assert reply == b"\x00"
