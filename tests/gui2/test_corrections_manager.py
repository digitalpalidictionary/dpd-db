import json
from pathlib import Path

from gui2.corrections_manager import _contributor_from_origin, _remove_key_from_file


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
