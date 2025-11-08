from contextlib import contextmanager

import pytest
from attrs import Factory, frozen

from lenlab.controller.auto_save import AutoSave
from lenlab.launchpad import protocol
from lenlab.spy import Spy


@pytest.fixture()
def auto_save():
    auto_save = AutoSave()
    auto_save.points.interval = 1.0
    return auto_save


@pytest.fixture()
def add_points(auto_save):
    def add_points(n: int = 1):
        payload = b"\xe0\x04\x00\x08" * n
        reply = protocol.pack(b"v", b"\x00\x00\x00\x00", 4 * n) + payload
        auto_save.points.parse_reply(reply)

    return add_points


@frozen
class MockFileObject:
    content: list[str] = Factory(list)

    def write(self, content: str):
        self.content.append(content)

    def get_content(self):
        return "".join(self.content)


@frozen
class MockPath:
    name: str
    mock_file_object: MockFileObject = Factory(MockFileObject)

    @contextmanager
    def open(self, mode):
        if mode == "w":
            del self.mock_file_object.content[:]
        yield self.mock_file_object

    def read_text(self) -> str:
        return self.mock_file_object.get_content()

    def get_lines(self) -> list[str]:
        return self.read_text().splitlines()


@pytest.fixture()
def mock_path(auto_save):
    mock_path = MockPath("data.csv")
    auto_save.save_as(mock_path)
    auto_save.auto_save.set(True)
    return mock_path


def test_clear(auto_save, add_points, mock_path):
    add_points(1)

    assert auto_save.points.unsaved
    assert auto_save.auto_save
    assert str(auto_save.file_path) == "data.csv"

    auto_save.clear()

    assert not auto_save.points.unsaved
    assert not auto_save.auto_save
    assert str(auto_save.file_path) == ""


def test_save_as_empty(auto_save, mock_path):
    content = mock_path.read_text()
    assert content.startswith("Lenlab")

    lines = mock_path.get_lines()
    assert len(lines) == 2


def test_save_as(auto_save, add_points):
    add_points(1)

    spy = Spy(auto_save.file_path.changed)

    mock_path = MockPath("data.csv")
    auto_save.save_as(mock_path)

    assert spy.get_single_arg() == "data.csv"

    content = mock_path.read_text()
    assert content.startswith("Lenlab")

    lines = mock_path.get_lines()
    assert len(lines) == 3
    assert lines[-1] == "0.000000; 1.005469; 1.650000"


def test_auto_save(auto_save, add_points, mock_path):
    add_points(5)
    auto_save.save()
    assert not auto_save.points.unsaved

    lines = mock_path.get_lines()
    assert len(lines) == 2 + 5


def test_auto_save_batches(auto_save, add_points, mock_path):
    add_points(3)
    auto_save.save()
    assert auto_save.points.unsaved

    lines = mock_path.get_lines()
    assert len(lines) == 2


def test_auto_save_everything(auto_save, add_points, mock_path):
    add_points(12)
    auto_save.save()
    assert not auto_save.points.unsaved

    lines = mock_path.get_lines()
    assert len(lines) == 2 + 12


def test_auto_save_twice(auto_save, add_points, mock_path):
    for i in range(2):
        add_points(5)
        auto_save.save()
        assert not auto_save.points.unsaved

        lines = mock_path.get_lines()
        assert len(lines) == 2 + (i + 1) * 5
