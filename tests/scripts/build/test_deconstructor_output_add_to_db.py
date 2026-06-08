"""Tests for scripts/build/deconstructor_output_add_to_db.py logic."""

import json
from pathlib import Path

import pytest

from tools.lookup_is_another_value import is_another_value

FIXTURE_PATH = (
    Path(__file__).parent / "test_deconstructor_output_add_to_db_fixtures.json"
)


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
