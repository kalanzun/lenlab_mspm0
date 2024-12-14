from ..message import Message
from ..model.launchpad import ti_pid, ti_vid
from ..model.lenlab import Lenlab
from ..model.port_info import PortInfo


def find_launchpad(port_infos: list[PortInfo]) -> list[PortInfo]:
    # vid, pid
    port_infos = [pi for pi in port_infos if pi.vid_pid == (ti_vid, ti_pid)]

    # cu*
    if matches := [pi for pi in port_infos if pi.name.startswith("cu")]:
        port_infos = matches

    # sort by number
    port_infos.sort(key=lambda pi: pi.sort_key)

    return port_infos


def discover(lenlab: Lenlab, port_infos: list[PortInfo]):
    matches = find_launchpad(port_infos)
    if not matches:
        lenlab.error.emit(NoLaunchpad())
        return

    lenlab.port_infos = matches


class NoLaunchpad(Message):
    english = "No launchpad found"
