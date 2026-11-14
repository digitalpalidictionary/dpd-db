import json
from pathlib import Path

import pytest

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


def _contributor(tmp_path: Path, monkeypatch) -> Pass1FileManager:
    monkeypatch.setenv("DPD_GUI2_DATA_DIR", str(tmp_path / "server_data"))
    paths = Gui2Paths.for_user("alice", base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    return Pass1FileManager(paths)


def _write_tracked(fm: Pass1FileManager, book: str, data: dict) -> Path:
    path = fm.gui2_data_path / f"pass1_auto_{book}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
    return path


class TestPrimaryRemove:
    def test_remove_deletes_the_word_from_the_file(self, tmp_path: Path):
        fm = _manager(tmp_path)
        fm.write("vv", {"a": 1, "b": 2})
        assert fm.remove("vv", "a") == {"b": 2}
        assert fm.read("vv") == {"b": 2}


class TestContributor:
    def test_read_hides_removed_words(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1, "b": 2})
        fm.remove("vv", "a")
        assert fm.read("vv") == {"b": 2}

    def test_remove_leaves_the_tracked_file_byte_identical(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        path = _write_tracked(fm, "vv", {"a": 1, "b": 2})
        before = path.read_bytes()
        fm.remove("vv", "a")
        assert path.read_bytes() == before

    def test_removal_survives_a_new_manager(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        fm.remove("vv", "a")
        assert _contributor(tmp_path, monkeypatch).read("vv") == {}

    def test_removed_word_stays_hidden_when_the_tracked_file_gains_words(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1, "b": 2})
        fm.remove("vv", "a")
        _write_tracked(fm, "vv", {"a": 1, "b": 2, "c": 3})
        assert fm.read("vv") == {"b": 2, "c": 3}

    def test_removals_are_per_book(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        _write_tracked(fm, "pv", {"a": 1})
        fm.remove("vv", "a")
        assert fm.read("pv") == {"a": 1}

    def test_removing_twice_lists_the_word_once(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        fm.remove("vv", "a")
        fm.remove("vv", "a")
        assert fm.removed_path is not None
        assert json.loads(fm.removed_path.read_text(encoding="utf-8")) == {"vv": ["a"]}

    def test_a_removals_file_that_is_not_an_object_is_ignored(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        assert fm.removed_path is not None
        fm.removed_path.parent.mkdir(parents=True, exist_ok=True)
        fm.removed_path.write_text("[]", encoding="utf-8")
        assert fm.read("vv") == {"a": 1}
        fm.remove("vv", "a")
        assert fm.read("vv") == {}

    def test_remove_leaves_no_temp_file_behind(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        fm.remove("vv", "a")
        assert fm.removed_path is not None
        assert [p.name for p in fm.removed_path.parent.glob("*.tmp")] == []

    def test_write_and_update_are_refused(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        path = _write_tracked(fm, "vv", {"a": 1})
        before = path.read_bytes()
        with pytest.raises(PermissionError):
            fm.write("vv", {})
        with pytest.raises(PermissionError):
            fm.update("vv", lambda d: d)
        assert path.read_bytes() == before


def _write_list(folder: Path, user: str, content: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"pass1_auto_removed_{user}.json"
    path.write_text(content, encoding="utf-8")
    return path


class TestSharedRemovedLists:
    def test_contributor_read_hides_every_contributors_words(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1, "b": 2, "c": 3, "d": 4})
        folder = tmp_path / "server_data"
        _write_list(folder, "alice", json.dumps({"vv": ["a"]}))
        _write_list(folder, "bob", json.dumps({"vv": ["b"], "pv": ["c"]}))
        assert fm.read("vv") == {"c": 3, "d": 4}

    def test_remove_writes_only_the_own_list(self, tmp_path: Path, monkeypatch):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1, "x": 2})
        folder = tmp_path / "server_data"
        bob = _write_list(folder, "bob", json.dumps({"vv": ["a"]}))
        before = bob.read_bytes()
        fm.remove("vv", "x")
        assert bob.read_bytes() == before
        assert json.loads((folder / "pass1_auto_removed_alice.json").read_text()) == {
            "vv": ["x"]
        }

    @pytest.mark.parametrize("content", ["{not json", '{"vv": "abc"}', '{"vv": [1]}'])
    def test_a_bad_list_hides_nothing(self, tmp_path: Path, monkeypatch, content: str):
        fm = _contributor(tmp_path, monkeypatch)
        _write_tracked(fm, "vv", {"a": 1})
        _write_list(tmp_path / "server_data", "bob", content)
        assert fm.read("vv") == {"a": 1}

    def test_the_laptop_read_ignores_pulled_lists(self, tmp_path: Path):
        fm = _manager(tmp_path)
        fm.write("vv", {"a": 1})
        _write_list(fm.gui2_data_path, "alice", json.dumps({"vv": ["a"]}))
        assert fm.read("vv") == {"a": 1}

    def test_finished_words_spans_contributors_for_one_book(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        folder = tmp_path / "server_data"
        _write_list(folder, "alice", json.dumps({"vv": ["a"]}))
        _write_list(folder, "bob", json.dumps({"vv": ["b"], "pv": ["c"]}))
        assert fm.finished_words("vv") == {"a", "b"}
        assert fm.finished_words("dn") == set()

    def test_finished_words_sees_a_list_written_after_the_manager_was_built(
        self, tmp_path: Path, monkeypatch
    ):
        fm = _contributor(tmp_path, monkeypatch)
        assert fm.finished_words("vv") == set()
        _write_list(tmp_path / "server_data", "bob", json.dumps({"vv": ["b"]}))
        assert fm.finished_words("vv") == {"b"}

    def test_finished_words_is_empty_on_the_laptop(self, tmp_path: Path):
        fm = _manager(tmp_path)
        _write_list(fm.gui2_data_path, "alice", json.dumps({"vv": ["a"]}))
        assert fm.finished_words("vv") == set()

    def test_all_removed_words_spans_lists_and_books(self, tmp_path: Path):
        fm = _manager(tmp_path)
        _write_list(fm.gui2_data_path, "alice", json.dumps({"vv": ["a"]}))
        _write_list(fm.gui2_data_path, "bob", json.dumps({"pv": ["b"], "vv": ["c"]}))
        assert fm.all_removed_words() == {"a", "b", "c"}
