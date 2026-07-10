from pathlib import Path

from gui2.filter_presets_manager import FilterPresetsManager
from gui2.paths import Gui2Paths
from gui2.toolkit import ToolKit


def _manager(tmp_path: Path) -> FilterPresetsManager:
    # bypass ToolKit.__init__ (flet.Page + live dpd.db) — FilterPresetsManager
    # only ever reads toolkit.paths.
    paths = Gui2Paths(base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    toolkit = object.__new__(ToolKit)
    toolkit.paths = paths
    return FilterPresetsManager(toolkit)


class TestNoPresets:
    def test_list_presets_is_empty(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.list_presets() == []

    def test_get_first_preset_is_none(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.get_first_preset() is None
        assert mgr.get_first_preset_name() is None


class TestSavePreset:
    def test_save_then_get(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [["root_key", ""]], ["id", "lemma_1"], 100)
        assert mgr.list_presets() == ["p1"]
        assert mgr.get_preset("p1") == {
            "data_filters": [["root_key", ""]],
            "display_filters": ["id", "lemma_1"],
            "limit": 100,
        }

    def test_persists_across_reload(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        reloaded = _manager(tmp_path)
        assert reloaded.get_preset("p1") == {
            "data_filters": [],
            "display_filters": ["id"],
            "limit": 0,
        }


class TestRenamePreset:
    def test_renames_existing(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        assert mgr.rename_preset("p1", "p2") is True
        assert mgr.list_presets() == ["p2"]

    def test_missing_old_name_returns_false(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        assert mgr.rename_preset("nonexistent", "p3") is False

    def test_new_name_already_taken_returns_false(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        mgr.save_preset("p2", [], ["id"], 0)
        assert mgr.rename_preset("p1", "p2") is False

    def test_same_name_returns_false(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        assert mgr.rename_preset("p1", "p1") is False


class TestDeletePreset:
    def test_deletes_existing(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        mgr.delete_preset("p1")
        assert mgr.list_presets() == []

    def test_deleting_missing_preset_is_a_no_op(self, tmp_path: Path):
        mgr = _manager(tmp_path)
        mgr.delete_preset("nonexistent")
        assert mgr.list_presets() == []
