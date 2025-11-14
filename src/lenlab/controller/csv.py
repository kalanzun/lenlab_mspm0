from collections.abc import Callable, Iterable
from importlib import metadata
from typing import Any

from attrs import frozen


@frozen
class CSVTemplate:
    name: str

    x: str = "time"
    ch1: str = "channel1"
    ch2: str = "channel2"

    x_format: str = ".3f"
    ch1_format: str = ".6f"
    ch2_format: str = ".6f"

    def head(self) -> str:
        version = metadata.version("lenlab")
        return f"Lenlab_MSPM0,{version},{self.name}\n{self.x},{self.ch1},{self.ch2}\n"

    def line_template(self) -> str:
        return f"%{self.x_format},%{self.ch1_format},%{self.ch2_format}\n"

    def write_rows(self, write: Callable[[str], Any], rows: Iterable[tuple[float, float, float]]):
        tpl = self.line_template()
        for row in rows:
            write(tpl % row)
