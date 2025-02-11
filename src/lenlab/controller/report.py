import logging
from io import StringIO
from typing import TextIO


class Report:
    file_name = "lenlab8-error-report.txt"
    file_format = "Text (*.txt)"

    def __init__(self):
        super().__init__()

        self.log = StringIO()
        handler = logging.StreamHandler(self.log)
        handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        logging.getLogger().addHandler(handler)

    def save_as(self, file: TextIO) -> None:
        file.write(self.log.getvalue())
