from io import StringIO

from lenlab.controller.report import Report


def test_report(logger):
    report = Report()

    logger.info("test message")

    file = StringIO()
    report.save_as(file)

    content = file.getvalue()
    assert content.endswith("test message\n")
