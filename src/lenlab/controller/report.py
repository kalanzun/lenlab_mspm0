import logging
from io import StringIO


class Report:
    file_name = "lenlab8-error-report.txt"
    file_format = "Text (*.txt)"

    def __init__(self):
        super().__init__()

        self.log = StringIO()
        handler = logging.StreamHandler(self.log)
        logging.getLogger().addHandler(handler)

    def save_as(self, file_name: str):
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(self.log.getvalue())
