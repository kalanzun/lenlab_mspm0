from importlib import metadata

from lenlab.controller.discovery import Discovery, NoLaunchpad, TivaLaunchpad
from lenlab.model.launchpad import lp_pid, ti_vid, tiva_pid
from lenlab.model.port_info import PortInfo
from lenlab.spy import Spy


def test_no_launchpad():
    discovery = Discovery()
    spy = Spy(discovery.error)

    available_ports = []
    discovery.discover(available_ports)

    assert discovery.available_terminals == []
    assert spy.is_single_message(NoLaunchpad)


def test_tiva_launchpad():
    discovery = Discovery()
    spy = Spy(discovery.error)

    available_ports = [PortInfo("tiva", ti_vid, tiva_pid)]
    discovery.discover(available_ports)

    assert discovery.available_terminals == []
    assert spy.is_single_message(TivaLaunchpad)


def test_no_rules():
    pass


def test_two_candidates():
    discovery = Discovery()

    available_ports = [PortInfo("uart", ti_vid, lp_pid), PortInfo("debug", ti_vid, lp_pid)]
    discovery.discover(available_ports)

    assert len(discovery.available_terminals) == 2
    assert discovery.available_terminals[0].port_info.name == "uart"


def test_two_candidates_select_first():
    discovery = Discovery()

    available_ports = [PortInfo("uart", ti_vid, lp_pid), PortInfo("debug", ti_vid, lp_pid)]
    discovery.discover(available_ports, select_first=True)

    assert len(discovery.available_terminals) == 1
    assert discovery.available_terminals[0].port_info.name == "uart"


def test_reverse_port_order():
    discovery = Discovery()

    available_ports = [PortInfo("debug", ti_vid, lp_pid), PortInfo("uart", ti_vid, lp_pid)]
    discovery.discover(available_ports)

    assert len(discovery.available_terminals) == 2
    assert discovery.available_terminals[1].port_info.name == "uart"


def test_single_candidate():
    discovery = Discovery()

    available_ports = [PortInfo("uart", ti_vid, lp_pid)]
    discovery.discover(available_ports)

    assert len(discovery.available_terminals) == 1
    assert discovery.available_terminals[0].port_info.name == "uart"


def test_no_permission():
    pass


def test_no_reply():
    pass


def test_slow_reply():
    pass


def test_old_firmware():
    pass


def test_current_firmware():
    version = metadata.version("lenlab")
    major, minor, *patch = version.split(".")
    fw_version = f"{major}.{minor}"
