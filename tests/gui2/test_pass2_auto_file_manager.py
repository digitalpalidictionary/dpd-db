from pathlib import Path

from gui2.pass2_auto_file_manager import Pass2AutoFileManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit


def _manager(tmp_path: Path) -> Pass2AutoFileManager:
    # bypass ToolKit.__init__ (flet.Page + live dpd.db) — Pass2AutoFileManager
    # only ever reads toolkit.paths.
    toolkit = object.__new__(ToolKit)
    toolkit.paths = Gui2Paths(base_dir=tmp_path)
    return Pass2AutoFileManager(toolkit)


class TestBasicCrud:
    def test_starts_empty(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.get_pass2_auto_data() == {}

    def test_update_then_get_headword(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.update_pass2_auto_data("1", {"lemma_1": "karoti"})
        assert mgr.get_headword("1") == {"lemma_1": "karoti"}

    def test_delete_existing_returns_true(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.update_pass2_auto_data("1", {"lemma_1": "karoti"})
        assert mgr.delete_item("1") is True
        assert mgr.get_pass2_auto_data() == {}

    def test_delete_missing_returns_false(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.delete_item("999") is False


class TestGetNextHeadwordData:
    def test_empty_returns_none_and_zero(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.get_next_headword_data() == (None, {}, 0)

    def test_pops_next_item_and_removes_it(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.update_pass2_auto_data("1", {"lemma_1": "karoti"})
        mgr.update_pass2_auto_data("2", {"lemma_1": "gacchati"})
        headword_id, data, remaining = mgr.get_next_headword_data()
        assert headword_id == "1"
        assert data == {"lemma_1": "karoti"}
        assert remaining == 2
        assert mgr.get_pass2_auto_data() == {"2": {"lemma_1": "gacchati"}}


class TestPersistence:
    def test_data_survives_reload_from_disk(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.update_pass2_auto_data("1", {"lemma_1": "karoti"})
        reloaded = _manager(tmp_path)
        assert reloaded.get_pass2_auto_data() == {"1": {"lemma_1": "karoti"}}
