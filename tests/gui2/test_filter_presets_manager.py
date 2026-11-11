from pathlib import Path

import pytest

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


class TestDamagedFileAndAtomicSave:
    def test_a_damaged_file_starts_empty_and_is_kept_aside(self, tmp_path: Path):

        paths = Gui2Paths(base_dir=tmp_path)
        paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
        paths.filter_presets_path.write_text("", encoding="utf-8")
        mgr = _manager(tmp_path)
        assert mgr.presets == {}
        assert (paths.gui2_data_path / "filter_presets.json.corrupt").exists()

    def test_a_save_leaves_no_temp_file(self, tmp_path: Path):
        import json

        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        data_dir = Gui2Paths(base_dir=tmp_path).gui2_data_path
        assert not list(data_dir.glob("*.tmp"))
        saved = (data_dir / "filter_presets.json").read_text(encoding="utf-8")
        assert saved == json.dumps(mgr.presets, ensure_ascii=False, indent=4)

    def test_a_failing_save_keeps_the_previous_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        mgr = _manager(tmp_path)
        mgr.save_preset("p1", [], ["id"], 0)
        path = Gui2Paths(base_dir=tmp_path).filter_presets_path
        good = path.read_text(encoding="utf-8")

        def broken(*args: object, **kwargs: object) -> str:
            raise RuntimeError("disk full")

        monkeypatch.setattr("gui2.filter_presets_manager.json.dumps", broken)
        with pytest.raises(RuntimeError):
            mgr.save_preset("p2", [], ["id"], 0)
        # The old truncate-then-write would have destroyed the file here.
        assert path.read_text(encoding="utf-8") == good


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
