import logging
from argparse import ArgumentParser
from collections.abc import Sequence

from lenlab import cli, flash, sys_info  # noqa: F401


def main(args: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)

    parser = ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        choices=cli.commands.keys(),
        default=next(iter(cli.commands.keys()), None),
    )

    namespace, unknown = parser.parse_known_args(args)
    return cli.commands[namespace.command](unknown)
