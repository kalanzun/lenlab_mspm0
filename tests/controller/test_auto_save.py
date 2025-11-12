import pytest

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
        payload = b"\xd9\x04\xff\x07" * n
        reply = protocol.pack(b"v", b"\x00\x00\x00\x00", 4 * n) + payload
        auto_save.points.parse_reply(reply)

    return add_points


@pytest.fixture()
def auto_save_path(auto_save, mock_path):
    auto_save.save_as(mock_path)
    auto_save.auto_save.set(True)
    return mock_path


def test_clear(auto_save, add_points, auto_save_path):
    add_points(1)

    assert auto_save.points.unsaved
    assert auto_save.auto_save
    assert str(auto_save.file_path) == "data.csv"

    auto_save.clear()

    assert not auto_save.points.unsaved
    assert not auto_save.auto_save
    assert str(auto_save.file_path) == ""


def test_save_as_empty(auto_save, auto_save_path):
    content = auto_save_path.read_text()
    assert content.startswith("Lenlab")

    assert auto_save_path.get_line_count() == 2


def test_save_as(auto_save, add_points, mock_path):
    add_points(1)

    spy = Spy(auto_save.file_path.changed)

    auto_save.save_as(mock_path)

    assert spy.get_single_arg() == "data.csv"

    content = mock_path.read_text()
    assert content.startswith("Lenlab")

    assert mock_path.get_line_count() == 3
    assert content.endswith("0.000,1.000073,1.649597\n")


def test_auto_save(auto_save, add_points, auto_save_path):
    add_points(5)
    auto_save.save_update()
    assert not auto_save.points.unsaved

    assert auto_save_path.get_line_count() == 2 + 5


def test_auto_save_batches(auto_save, add_points, auto_save_path):
    add_points(3)
    auto_save.save_update()
    assert auto_save.points.unsaved

    assert auto_save_path.get_line_count() == 2


def test_auto_save_everything(auto_save, add_points, auto_save_path):
    add_points(12)
    auto_save.save_update()
    assert not auto_save.points.unsaved

    assert auto_save_path.get_line_count() == 2 + 12


def test_auto_save_twice(auto_save, add_points, auto_save_path):
    for i in range(2):
        add_points(5)
        auto_save.save_update()
        assert not auto_save.points.unsaved

        assert auto_save_path.get_line_count() == 2 + (i + 1) * 5
