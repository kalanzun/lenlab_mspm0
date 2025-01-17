import argparse
import logging
from importlib import metadata

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--preview",
        action="store_true",
        help="run startup code for testing but do not show user interface",
    )

    args = parser.parse_args(argv)

    version = metadata.version("lenlab")
    logger.info(f"Lenlab {version}")

    if args.preview:
        return
