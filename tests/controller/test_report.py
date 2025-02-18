import logging
from io import StringIO

from lenlab.controller.report import Report

logger = logging.getLogger(__name__)


def test_report():
    # this test requires --log-cli-level=INFO, else it fails

    report = Report()

    logger.info("test message")

    file = StringIO()
    report.save_as(file)

    content = file.getvalue()
    assert content.endswith("test message\n")
