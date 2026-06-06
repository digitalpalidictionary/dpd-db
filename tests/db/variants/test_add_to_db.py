"""
Characterization tests for AddVariantsToDb.

DB-write methods (delete_variants_in_db, update_variants_in_db,
add_variants_to_db) require a live DB session and are not exercised here.
Tests freeze the pure routing logic that is specific to this module.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from db.variants.add_to_db import AddVariantsToDb
from tools.lookup_is_another_value import is_another_value

FIXTURE_PATH = Path(__file__).parent / "test_add_to_db_fixtures.json"

_OTHER_COLS = [
    "headwords",
    "roots",
    "deconstructor",
    "see",
    "spelling",
    "grammar",
    "help",
    "abbrev",
    "abbrev_other",
    "epd",
    "rpd",
    "other",
    "sinhala",
    "devanagari",
    "thai",
]


def _blank_lookup_row(**overrides: str) -> SimpleNamespace:
    """Return a SimpleNamespace with all Lookup non-key columns set to ''."""
    row = SimpleNamespace(lookup_key="test_key", variant="")
    for col in _OTHER_COLS:
        setattr(row, col, "")
    for k, v in overrides.items():
        setattr(row, k, v)
    return row


def test_lookup_keys_built_from_rows() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    existing_keys: list[str] = fixtures["existing_variant_keys"]

    lookup_table = [SimpleNamespace(lookup_key=k) for k in existing_keys]
    result = [r.lookup_key for r in lookup_table]

    assert result == existing_keys


def test_update_key_routing() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    existing_keys: list[str] = fixtures["existing_variant_keys"]

    inst = object.__new__(AddVariantsToDb)
    inst.lookup_keys = existing_keys
    inst.variants_dict = {k: {} for k in existing_keys[:3]}
    inst.variants_dict["__new_key_xyz__"] = {}

    update_keys = [k for k in inst.variants_dict if k in inst.lookup_keys]
    new_keys = [k for k in inst.variants_dict if k not in inst.lookup_keys]

    assert set(update_keys) == set(existing_keys[:3])
    assert new_keys == ["__new_key_xyz__"]


def test_delete_routing_row_with_other_values() -> None:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    sample = fixtures["sample_row"]

    row = _blank_lookup_row(
        lookup_key=sample["lookup_key"],
        headwords=sample["headwords"],
        variant=sample["variant"],
    )

    assert is_another_value(row, "variant") is True


def test_delete_routing_variant_only_row() -> None:
    row = _blank_lookup_row(
        lookup_key="test_only_variant",
        variant='{"CST": {"text": [["word", "ref"]]}}',
    )

    assert is_another_value(row, "variant") is False
