from importlib import metadata
from typing import TextIO

from attrs import frozen


@frozen
class CSVWriter:
    name: str
    x: str = "time"
    ch1: str = "channel1"
    ch2: str = "channel2"
    x_format: str = ".6f"
    ch1_format: str = ".6f"
    ch2_format: str = ".6f"

    def write_head(self, file: TextIO):
        version = metadata.version("lenlab")
        file.write(f"Lenlab_MSPM0,{version},{self.name}\n")
        file.write(f"{self.x},{self.ch1},{self.ch2}\n")

    def write_data(self, file: TextIO, x, ch1, ch2):
        line_template = f"%{self.x_format},%{self.ch1_format},%{self.ch2_format}\n"
        for _x, _ch1, _ch2 in zip(x, ch1, ch2, strict=False):
            file.write(line_template % (_x, _ch1, _ch2))
