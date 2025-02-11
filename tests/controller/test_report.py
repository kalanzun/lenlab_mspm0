import logging
from io import StringIO

from lenlab.controller.report import Report

logger = logging.getLogger(__name__)


def test_report():
    report = Report()

    logger.info("test message")

    file = StringIO()
    report.save_as(file)

    assert file.getvalue().endswith("test message\n")
