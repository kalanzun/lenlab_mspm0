from lenlab.cli import main


def test_cli():
    main()


def test_main():
    from lenlab import __main__

    assert __main__
