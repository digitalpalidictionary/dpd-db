from pathlib import Path

from gui2.history import HistoryManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit


def _manager(tmp_path: Path, max_size: int = 20) -> HistoryManager:
    # bypass ToolKit.__init__ (flet.Page + live dpd.db) — HistoryManager only
    # ever reads toolkit.paths.
    toolkit = object.__new__(ToolKit)
    toolkit.paths = Gui2Paths(base_dir=tmp_path)
    return HistoryManager(toolkit, max_size=max_size)


class TestEmptyHistory:
    def test_starts_empty(self, tmp_path: Path):
        hm = _manager(tmp_path)
        assert hm.get_history() == []


class TestAddItem:
    def test_new_item_is_not_already_first(self, tmp_path: Path):
        hm = _manager(tmp_path)
        assert hm.add_item(1, "karoti") is True
        assert hm.get_history() == [{"id": 1, "lemma_1": "karoti"}]

    def test_re_adding_current_first_item_reports_already_first(self, tmp_path: Path):
        hm = _manager(tmp_path)
        hm.add_item(1, "karoti")
        assert hm.add_item(1, "karoti") is False

    def test_adding_second_item_puts_it_first(self, tmp_path: Path):
        hm = _manager(tmp_path)
        hm.add_item(1, "karoti")
        hm.add_item(2, "gacchati")
        assert hm.get_history() == [
            {"id": 2, "lemma_1": "gacchati"},
            {"id": 1, "lemma_1": "karoti"},
        ]

    def test_re_adding_non_first_item_moves_it_to_front_without_duplicating(
        self, tmp_path: Path
    ):
        hm = _manager(tmp_path)
        hm.add_item(1, "karoti")
        hm.add_item(2, "gacchati")
        result = hm.add_item(1, "karoti")
        assert result is True
        assert hm.get_history() == [
            {"id": 1, "lemma_1": "karoti"},
            {"id": 2, "lemma_1": "gacchati"},
        ]

    def test_truncates_to_max_size(self, tmp_path: Path):
        hm = _manager(tmp_path, max_size=3)
        hm.add_item(1, "a")
        hm.add_item(2, "b")
        hm.add_item(3, "c")
        hm.add_item(4, "d")
        assert hm.get_history() == [
            {"id": 4, "lemma_1": "d"},
            {"id": 3, "lemma_1": "c"},
            {"id": 2, "lemma_1": "b"},
        ]

    def test_persists_across_reload(self, tmp_path: Path):
        hm = _manager(tmp_path)
        hm.add_item(1, "karoti")
        reloaded = _manager(tmp_path)
        assert reloaded.get_history() == [{"id": 1, "lemma_1": "karoti"}]


class TestRefreshCallbacks:
    def test_registered_callback_is_invoked_on_add(self, tmp_path: Path):
        hm = _manager(tmp_path)
        calls = []
        hm.register_refresh_callback(lambda: calls.append(1))
        hm.add_item(1, "karoti")
        assert calls == [1]
