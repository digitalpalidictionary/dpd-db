"""Tests for scripts/build/sanskrit_root_families_updater.py

Fixtures were captured from the current code against dpd.db before any
refactoring. Tests assert byte-identical output so a refactor cannot silently
change how a RootFamily is built from a headword.

Coverage:
    RootFamily.__init__ — normal branch (i.rt present) with a sanskrit root
                          family resolved from the tsv, plus the empty
                          sanskrit_clean case (sanskrit_dump == {""}).
    remove_sanskrit_root_family — real-data no-ops (the substitution never
                          fires on current data, proven across the whole db),
                          plus literal cases that lock in the fixed boundary
                          behaviour: a standalone token is stripped, but a
                          token embedded mid-word is left intact. The old
                          pattern `(^|, ||\\b)` wrongly stripped `kar` from
                          `akar` -> `a`; the fixed `(^|, |\\b)` keeps `akar`.

Not covered (no real data exists): the i.rt-is-None error guard, and the
"key absent from tsv" fallback — every root_family_key in the db is present
in root_families_sanskrit.tsv, which is regenerated from the db.
"""

import json
from pathlib import Path

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.build.sanskrit_root_families_updater import (
    RootFamily,
    import_tsv_to_dict,
    remove_sanskrit_root_family,
)
from tools.paths import ProjectPaths

FIXTURE_PATH = (
    Path(__file__).parent / "test_sanskrit_root_families_updater_fixtures.json"
)
DB_PATH = Path("dpd.db")


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def db():
    return get_db_session(DB_PATH)


@pytest.fixture(scope="module")
def tsv_dict() -> dict[str, str]:
    return import_tsv_to_dict(ProjectPaths())


def test_root_family_matches_frozen_output(db, fixtures, tsv_dict) -> None:
    """RootFamily(i, tsv_dict) reproduces the frozen attributes for every case."""
    for key, fixture in fixtures.items():
        if key == "remove_sanskrit_root_family":
            continue
        hw = db.query(DpdHeadword).filter_by(id=fixture["input"]["id"]).first()
        assert hw is not None, f"missing headword id {fixture['input']['id']}"

        rf = RootFamily(hw, tsv_dict)
        expected = fixture["output"]
        actual = {
            "root_key": rf.root_key,
            "root_group": rf.root_group,
            "root_sign": rf.root_sign,
            "root_meaning": rf.root_meaning,
            "sanskrit_root": rf.sanskrit_root,
            "sanskrit_root_class": rf.sanskrit_root_class,
            "sanskrit_root_meaning": rf.sanskrit_root_meaning,
            "pali_root_family": rf.pali_root_family,
            "sanskrit_root_family": rf.sanskrit_root_family,
            "sanskrit_dump": sorted(rf.sanskrit_dump),
        }
        assert actual == expected, f"mismatch for {hw.lemma_1}"


def test_remove_sanskrit_root_family_real_noops(db, fixtures, tsv_dict) -> None:
    """On real db data the substitution never changes the sanskrit string."""
    for case in fixtures["remove_sanskrit_root_family"]["real_noops"]:
        hw = db.query(DpdHeadword).filter_by(id=case["id"]).first()
        assert hw is not None, f"missing headword id {case['id']}"
        srf = tsv_dict.get(hw.root_family_key, "")
        assert srf == case["sanskrit_root_family"]
        result = remove_sanskrit_root_family(hw.sanskrit_clean, srf)
        assert result == case["result"] == hw.sanskrit_clean


def test_remove_sanskrit_root_family_literal_cases(fixtures) -> None:
    """Standalone tokens are stripped; mid-word tokens are left intact."""
    for case in fixtures["remove_sanskrit_root_family"]["literal_cases"]:
        result = remove_sanskrit_root_family(
            case["sanskrit"], case["sanskrit_root_family"]
        )
        assert result == case["result"], (
            f"{case['sanskrit']!r} / {case['sanskrit_root_family']!r}"
        )
