from pathlib import Path

from gui2.pass1_file_manager import Pass1FileManager
from gui2.paths import Gui2Paths


def _manager(tmp_path: Path) -> Pass1FileManager:
    paths = Gui2Paths(base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True)
    return Pass1FileManager(paths)


class TestRead:
    def test_missing_file_returns_empty_dict(self, tmp_path: Path):
        fm = _manager(tmp_path)
        assert fm.read("dn") == {}

    def test_corrupted_json_returns_empty_dict(self, tmp_path: Path):
        fm = _manager(tmp_path)
        (fm.gui2_data_path / "pass1_auto_dn.json").write_text(
            "{not json", encoding="utf-8"
        )
        assert fm.read("dn") == {}


class TestWrite:
    def test_write_then_read_round_trips(self, tmp_path: Path):
        fm = _manager(tmp_path)
        fm.write("dn", {"a": 1})
        assert fm.read("dn") == {"a": 1}

    def test_write_is_scoped_per_book(self, tmp_path: Path):
        fm = _manager(tmp_path)
        fm.write("dn", {"a": 1})
        fm.write("mn", {"b": 2})
        assert fm.read("dn") == {"a": 1}
        assert fm.read("mn") == {"b": 2}


class TestUpdate:
    def test_update_function_mutates_and_persists(self, tmp_path: Path):
        fm = _manager(tmp_path)
        fm.write("dn", {"a": 1})

        def upd(data: dict) -> str:
            data["b"] = 2
            return "done"

        result = fm.update("dn", upd)
        assert result == "done"
        assert fm.read("dn") == {"a": 1, "b": 2}

    def test_update_on_missing_file_starts_from_empty_dict(self, tmp_path: Path):
        fm = _manager(tmp_path)

        def upd(data: dict) -> None:
            data["new"] = True

        fm.update("dn", upd)
        assert fm.read("dn") == {"new": True}
