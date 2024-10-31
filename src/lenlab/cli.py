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
    import pytest

    test_args = [
        "--pyargs",
        "lenlab.tests.test_sys_info",
        "--log-cli-level",
        "INFO",
        "--log-file",
        "sys_info.log",
    ]
    # later arguments replace previous arguments
    test_args.extend(args)
    return pytest.main(test_args)


@command
def test(args):
    import pytest

    test_args = [
        "--pyargs",
        "lenlab.tests",
        "--log-cli-level",
        "INFO",
    ]
    # later arguments replace previous arguments
    test_args.extend(args)
    return pytest.main(test_args)


@command
def stress(args):
    """about 10 minutes"""
    import pytest

    test_args = [
        "--pyargs",
        "lenlab.tests.test_comm::test_28k",
        "--count=2000",
    ]
    # later arguments replace previous arguments
    test_args.extend(args)
    return pytest.main(test_args)


@command
def flash(args):
    import pytest

    test_args = [
        "--pyargs",
        "lenlab.tests.test_bsl::test_flash",
        "--log-cli-level",
        "INFO",
        "--flash",
    ]
    # later arguments replace previous arguments
    test_args.extend(args)
    print(test_args)
    return pytest.main(test_args)
