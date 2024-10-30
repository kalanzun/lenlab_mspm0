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

    namespace = parser.parse_args(args)
    return commands[namespace.command]()


@command
def sys_info():
    import pytest

    return pytest.main(
        [
            "--pyargs",
            "lenlab.tests.test_sys_info",
            "--log-cli-level",
            "INFO",
            "--log-file",
            "sys_info.log",
        ]
    )


@command
def test():
    import pytest

    return pytest.main(
        [
            "--pyargs",
            "lenlab.tests",
            "--log-cli-level",
            "INFO",
        ]
    )


@command
def comm_test():
    import pytest

    return pytest.main(
        [
            "--pyargs",
            "lenlab.tests.test_comm::test_28k",
            "--count=2000",
        ]
    )
