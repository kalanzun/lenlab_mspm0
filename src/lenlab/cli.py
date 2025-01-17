import argparse
import logging
import sys
from importlib import metadata

from .controller.discovery import Discovery
from .model.port_info import PortInfo

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--port",
        action="store",
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="run startup code for testing but do not show user interface",
    )

    args = parser.parse_args(argv)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    discovery = Discovery()
    discovery.error.connect(logger.error)

    if args.port:
        available_ports = [PortInfo.from_port_name(args.port)]
    else:
        available_ports = PortInfo.available_ports()

    discovery.discover(available_ports, select_first=sys.platform != "win32")

    if args.preview:
        return
