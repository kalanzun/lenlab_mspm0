from .port_info import PortInfo

ti_vid = 0x0451
ti_pid = 0xBEF3


def find_launchpad(port_infos: list[PortInfo]) -> list[PortInfo]:
    # vid, pid
    port_infos = [pi for pi in port_infos if pi.vid_pid == (ti_vid, ti_pid)]

    # cu*
    if matches := [pi for pi in port_infos if pi.name.startswith("cu")]:
        port_infos = matches

    # sort by number
    port_infos.sort(key=lambda pi: pi.sort_key)

    return port_infos