import logging
import time
from functools import partial
from operator import mod
from pathlib import Path

import numpy as np
import pytest

from lenlab.controller.csv import CSVTemplate

logger = logging.getLogger(__name__)


@pytest.fixture()
def example():
    return np.empty((1_000_000,))


@pytest.fixture()
def tmp_file(tmp_path: Path):
    return tmp_path / "example.csv"


@pytest.fixture()
def csv_template():
    return CSVTemplate("test")


class RuntimeProbe:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.runtime = time.time() - self.start

    def __str__(self):
        return f"runtime: {self.runtime * 1e3:.0f} ms"


def test_format_map_writelines(tmp_file: Path, example: np.ndarray):
    # writelines and format are slow
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        file.writelines(map("{0:.6f}\n".format, example))

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_mod_map_writelines(tmp_file: Path, example: np.ndarray):
    # mod is faster than format
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        file.writelines(map(partial(mod, "%.6f\n"), example))

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_format_join_write(tmp_file: Path, example: np.ndarray):
    # join write is faster than writelines
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        file.write("".join(map("{0:.6f}\n".format, example)))

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_mod_join_write(tmp_file: Path, example: np.ndarray):
    # this one is fast
    # join write is faster than writelines
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        file.write("".join(map(partial(mod, "%.6f\n"), example)))

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_for_loop_f_string(tmp_file: Path, example: np.ndarray):
    # faster than format, slow overall
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        for row in example:
            file.write(f"{row:.6f}\n")

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_for_loop_mod(tmp_file: Path, example: np.ndarray):
    # faster than writelines, slower than join write
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        for row in example:
            file.write("%.6f\n" % (row,))  # noqa

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)


def test_for_loop_mod_local(tmp_file: Path, example: np.ndarray):
    # this one is fast
    with RuntimeProbe() as probe, tmp_file.open("w", encoding="utf-8") as file:
        write = file.write
        tpl = "{%.6f}\n"
        for row in example:
            write(tpl % (row,))

    assert tmp_file.read_text(encoding="utf-8")
    logger.info(probe)
