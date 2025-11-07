from contextlib import contextmanager
from pathlib import Path

import pytest
from attrs import Factory, frozen

from lenlab.controller.auto_save import AutoSave
from lenlab.launchpad import protocol
from lenlab.model.points import Points
from lenlab.spy import Spy


@pytest.fixture()
def points():
    return Points(1.0)


@pytest.fixture()
def add_points(points):
    def add_points(n: int = 1):
        payload = b"\xe0\x04\x00\x08" * n
        reply = protocol.pack(b"v", b"\x00\x00\x00\x00", 4 * n) + payload
        points.parse_reply(reply)

    return add_points


@pytest.fixture()
def auto_save(points):
    auto_save = AutoSave()
    auto_save.set_points(points)
    return auto_save


@frozen
class MockFileObject:
    content: list[str] = Factory(list)

    def write(self, content: str):
        self.content.append(content)

    def get_value(self):
        return "".join(self.content)


@frozen
class MockPath:
    name: str
    file_object: MockFileObject = Factory(MockFileObject)

    @contextmanager
    def open(self, mode):
        if mode == "w":
            del self.file_object.content[:]
        yield self.file_object


@pytest.fixture()
def file_path():
    return MockPath("data.csv")


def test_set_points_resets_properties(points):
    auto_save = AutoSave()

    auto_save.set_unsaved(True)
    auto_save.set_auto_save(True)
    auto_save.set_file_path(Path())

    unsaved_changed = Spy(auto_save.unsaved_changed)
    auto_save_changed = Spy(auto_save.auto_save_changed)
    file_path_changed = Spy(auto_save.file_path_changed)

    auto_save.set_points(points)

    assert unsaved_changed.get_single_arg() is False
    assert auto_save.unsaved is False

    assert auto_save_changed.get_single_arg() is False
    assert auto_save.auto_save is False

    assert file_path_changed.get_single_arg() == ""
    assert auto_save.file_path is None


def test_set_points_unsaved(points, add_points):
    add_points(1)

    auto_save = AutoSave()
    auto_save.set_points(points)

    assert auto_save.unsaved is True


def test_save_as_empty(auto_save, file_path):
    auto_save.save_as(file_path)

    content = file_path.file_object.get_value()
    assert content.startswith("Lenlab")
    assert len(content.splitlines()) == 2


def test_save_as(auto_save, add_points, file_path):
    add_points(1)

    spy = Spy(auto_save.file_path_changed)
    auto_save.save_as(file_path)

    content = file_path.file_object.get_value()
    assert content.startswith("Lenlab")
    lines = content.splitlines()
    assert len(lines) == 3
    assert lines[-1] == "0.000000; 1.005469; 1.650000"

    assert spy.get_single_arg() == "data.csv"


def test_auto_save(auto_save, add_points, file_path):
    auto_save.save_as(file_path)
    auto_save.set_auto_save(True)

    add_points(5)
    auto_save.set_unsaved(True)

    auto_save.save()
    assert auto_save.unsaved is False

    lines = file_path.file_object.get_value().splitlines()
    assert len(lines) == 2 + 5


def test_auto_save_batches(auto_save, add_points, file_path):
    auto_save.save_as(file_path)
    auto_save.set_auto_save(True)

    add_points(3)
    auto_save.set_unsaved(True)

    auto_save.save()
    assert auto_save.unsaved is True

    lines = file_path.file_object.get_value().splitlines()
    assert len(lines) == 2


def test_auto_save_everything(auto_save, add_points, file_path):
    auto_save.save_as(file_path)
    auto_save.set_auto_save(True)

    add_points(12)
    auto_save.set_unsaved(True)

    auto_save.save()
    assert auto_save.unsaved is False

    lines = file_path.file_object.get_value().splitlines()
    assert len(lines) == 2 + 12


def test_auto_save_twice(auto_save, add_points, file_path):
    auto_save.save_as(file_path)
    auto_save.set_auto_save(True)

    for i in range(2):
        add_points(5)
        auto_save.set_unsaved(True)

        auto_save.save()
        assert auto_save.unsaved is False

        lines = file_path.file_object.get_value().splitlines()
        assert len(lines) == 2 + (i + 1) * 5
