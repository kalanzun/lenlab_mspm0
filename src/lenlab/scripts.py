from argparse import ArgumentParser
from collections.abc import Sequence

from . import cli
from . import sys_info


def main(args: Sequence[str] | None = None) -> int:
    parser = ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        choices=cli.commands.keys(),
        default=next(iter(cli.commands.keys()), None),
    )

    namespace, unknown = parser.parse_known_args(args)
    return cli.commands[namespace.command](unknown)
