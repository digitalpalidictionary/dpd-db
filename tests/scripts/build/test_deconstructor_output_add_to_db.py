"""Tests for scripts/build/deconstructor_output_add_to_db.py logic."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.lookup_is_another_value import is_another_value
from tools.update_test_add import update_test_add

FIXTURE_PATH = (
    Path(__file__).parent / "test_deconstructor_output_add_to_db_fixtures.json"
)


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class TestUpdateTestAdd:
    def test_update_set_contains_intersection(self, fixtures: dict) -> None:
        """Keys in both lookup and dict land in update_set."""
        data = fixtures["update_test_add"]
        lookup_keys = data["lookup_keys"]
        dict_keys = data["dict_keys"]

        lookup_rows = [SimpleNamespace(lookup_key=k) for k in lookup_keys]
        the_dict = {k: [] for k in dict_keys}

        update_set, test_set, add_set = update_test_add(lookup_rows, the_dict)  # type: ignore[arg-type]

        expected_update = set(lookup_keys) & set(dict_keys)
        assert update_set == expected_update

    def test_test_set_is_lookup_only(self, fixtures: dict) -> None:
        """Keys only in lookup land in test_set."""
        data = fixtures["update_test_add"]
        lookup_keys = data["lookup_keys"]
        dict_keys = data["dict_keys"]

        lookup_rows = [SimpleNamespace(lookup_key=k) for k in lookup_keys]
        the_dict = {k: [] for k in dict_keys}

        update_set, test_set, add_set = update_test_add(lookup_rows, the_dict)  # type: ignore[arg-type]

        expected_test = set(lookup_keys) - set(dict_keys)
        assert test_set == expected_test

    def test_add_set_is_dict_only(self, fixtures: dict) -> None:
        """Keys only in dict land in add_set."""
        data = fixtures["update_test_add"]
        lookup_keys = data["lookup_keys"]
        dict_keys = data["dict_keys"]

        lookup_rows = [SimpleNamespace(lookup_key=k) for k in lookup_keys]
        the_dict = {k: [] for k in dict_keys}

        update_set, test_set, add_set = update_test_add(lookup_rows, the_dict)  # type: ignore[arg-type]

        expected_add = set(dict_keys) - set(lookup_keys)
        assert add_set == expected_add

    def test_sets_are_disjoint(self, fixtures: dict) -> None:
        """The three sets have no overlap."""
        data = fixtures["update_test_add"]
        lookup_rows = [SimpleNamespace(lookup_key=k) for k in data["lookup_keys"]]
        the_dict = {k: [] for k in data["dict_keys"]}

        update_set, test_set, add_set = update_test_add(lookup_rows, the_dict)  # type: ignore[arg-type]

        assert not (update_set & test_set)
        assert not (update_set & add_set)
        assert not (test_set & add_set)

    def test_empty_lookup(self) -> None:
        the_dict = {"a": ["x"], "b": ["y"]}
        update_set, test_set, add_set = update_test_add([], the_dict)  # type: ignore[arg-type]
        assert update_set == set()
        assert test_set == set()
        assert add_set == {"a", "b"}

    def test_empty_dict(self) -> None:
        lookup_rows = [SimpleNamespace(lookup_key="x"), SimpleNamespace(lookup_key="y")]
        update_set, test_set, add_set = update_test_add(lookup_rows, {})  # type: ignore[arg-type]
        assert update_set == set()
        assert test_set == {"x", "y"}
        assert add_set == set()


class TestIsAnotherValue:
    def test_real_row_has_another_value(self, fixtures: dict) -> None:
        """A row with headwords set reports another value when checking deconstructor."""
        data = fixtures["is_another_value_row"]
        from db.models import Lookup

        row = Lookup()
        row.lookup_key = data["lookup_key"]
        row.headwords = data["headwords"]
        row.deconstructor = data["deconstructor"]

        result = is_another_value(row, "deconstructor")
        assert result == data["is_another_value_result"]

    def test_no_other_value(self) -> None:
        """A row with only deconstructor set returns False."""
        from db.models import Lookup

        row = Lookup()
        row.lookup_key = "test"
        row.deconstructor = '["a + b"]'

        assert is_another_value(row, "deconstructor") is False


class TestDeconstructorPack:
    def test_pack_produces_correct_json(self, fixtures: dict) -> None:
        """deconstructor_pack writes JSON-serialised list to .deconstructor."""
        from db.models import Lookup

        data = fixtures["deconstructor_pack"]
        row = Lookup()

        row.deconstructor_pack(data["input"])
        assert row.deconstructor == data["expected_json"]

    def test_pack_unpack_roundtrip(self, fixtures: dict) -> None:
        """deconstructor_unpack reverses deconstructor_pack exactly."""
        from db.models import Lookup

        data = fixtures["deconstructor_pack"]
        row = Lookup()

        row.deconstructor_pack(data["input"])
        assert row.deconstructor_unpack == data["input"]
