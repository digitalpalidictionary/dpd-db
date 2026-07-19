import json
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from gui2.corrections_manager import (
    CorrectionsManager,
    _contributor_from_origin,
    _remove_key_from_file,
)
from gui2.paths import Gui2Paths

if TYPE_CHECKING:
    from db.models import DpdHeadword
    from gui2.toolkit import ToolKit


class _FakeWord:
    def __init__(self, id: int, lemma_1: str) -> None:
        self.id = id
        self.lemma_1 = lemma_1


def _fake_toolkit(paths: Gui2Paths) -> "ToolKit":
    return cast("ToolKit", SimpleNamespace(paths=paths))


def _fake_word(id: int, lemma_1: str) -> "DpdHeadword":
    return cast("DpdHeadword", _FakeWord(id, lemma_1))


def _manager(tmp_path: Path, username: str) -> CorrectionsManager:
    paths = Gui2Paths.for_user(username, base_dir=tmp_path)
    paths.gui2_data_path.mkdir(parents=True, exist_ok=True)
    return CorrectionsManager(_fake_toolkit(paths))


class TestContributorFromOrigin:
    def test_none_origin_is_primary(self):
        assert _contributor_from_origin(None, prefix="corrections_") == "primary"

    def test_prefixed_stem_strips_prefix(self):
        origin = Path("corrections_bob.json")
        assert _contributor_from_origin(origin, prefix="corrections_") == "bob"

    def test_non_prefixed_stem_returned_as_is(self):
        origin = Path("weird_name.json")
        assert _contributor_from_origin(origin, prefix="corrections_") == "weird_name"


class TestRemoveKeyFromFile:
    def test_removes_key_and_keeps_remaining_data(self, tmp_path: Path):
        path = tmp_path / "f.json"
        path.write_text(json.dumps({"1": {"a": 1}, "2": {"b": 2}}), encoding="utf-8")
        _remove_key_from_file(path, "1")
        assert json.loads(path.read_text(encoding="utf-8")) == {"2": {"b": 2}}

    def test_removing_last_key_writes_empty_object(self, tmp_path: Path):
        path = tmp_path / "f.json"
        path.write_text(json.dumps({"1": {"a": 1}}), encoding="utf-8")
        _remove_key_from_file(path, "1")
        assert path.read_text(encoding="utf-8") == "{}"

    def test_missing_key_leaves_file_unchanged(self, tmp_path: Path):
        path = tmp_path / "f.json"
        path.write_text(json.dumps({"1": {"a": 1}}), encoding="utf-8")
        _remove_key_from_file(path, "not_present")
        assert json.loads(path.read_text(encoding="utf-8")) == {"1": {"a": 1}}

    def test_missing_file_does_not_raise(self, tmp_path: Path):
        path = tmp_path / "missing.json"
        _remove_key_from_file(path, "1")
        assert not path.exists()


class TestUpdateCorrectionsKey:
    def test_update_uses_username_id_key_with_id_inside_entry(self, tmp_path: Path):
        mgr = _manager(tmp_path, "bob")
        mgr.update_corrections(_fake_word(42, "gacchati"), "a note")
        (key,) = mgr.corrections_dict.keys()
        assert key == "bob_42"
        entry = mgr.corrections_dict[key]
        assert entry["id"] == 42
        assert entry["comment"] == "a note"

    def test_recorrecting_same_id_updates_in_place_latest_wins(self, tmp_path: Path):
        mgr = _manager(tmp_path, "bob")
        mgr.update_corrections(_fake_word(42, "testa"), "first")
        (key_after_first,) = mgr.corrections_dict.keys()
        mgr.update_corrections(_fake_word(42, "testa"), "second")
        assert list(mgr.corrections_dict.keys()) == [key_after_first]
        assert mgr.corrections_dict[key_after_first]["comment"] == "second"

    def test_different_ids_get_separate_entries(self, tmp_path: Path):
        mgr = _manager(tmp_path, "bob")
        mgr.update_corrections(_fake_word(42, "testa"), "a")
        mgr.update_corrections(_fake_word(43, "testa 2"), "b")
        assert len(mgr.corrections_dict) == 2


class TestPrimaryQueueMixedKeys:
    def test_mixed_old_and_new_key_file_processes_and_removes_both(
        self, tmp_path: Path
    ):
        data_dir = tmp_path / "gui2" / "data"
        data_dir.mkdir(parents=True)
        contrib = data_dir / "corrections_bob.json"
        new_key = str(uuid.uuid4())
        contrib.write_text(
            json.dumps(
                {
                    "123": {"id": 123, "lemma_1": "legacy"},
                    new_key: {"id": 456, "lemma_1": "modern"},
                }
            ),
            encoding="utf-8",
        )

        paths = Gui2Paths(base_dir=tmp_path)  # primary user (corrections.json)
        mgr = CorrectionsManager(_fake_toolkit(paths))
        assert len(mgr.corrections_dict) == 2

        seen_keys: list[str] = []
        for _ in range(2):
            correction, origin, source_key, _ = mgr.get_next_correction()
            assert correction is not None and source_key is not None
            seen_keys.append(source_key)
            # NOTE: word_data["id"] deliberately differs from the uuid source_key
            # to prove removal keys off source_key, not the entry id.
            mgr.save_processed_correction(
                {"id": str(correction["id"])}, origin, source_key
            )

        assert set(seen_keys) == {"123", new_key}
        assert json.loads(contrib.read_text(encoding="utf-8")) == {}
