from argparse import ArgumentParser
from collections.abc import Sequence

commands = dict()


def command(fn):
    global commands
    commands[fn.__name__] = fn
    return fn


def main(args: Sequence[str] | None = None) -> int:
    global commands
    parser = ArgumentParser()

    parser.add_argument(
        "command",
        nargs="?",
        choices=commands.keys(),
        default=next(iter(commands.keys()), None),
    )

    namespace, unknown = parser.parse_known_args(args)
    return commands[namespace.command](unknown)


@command
def sys_info(args):
    print("sys_info")
