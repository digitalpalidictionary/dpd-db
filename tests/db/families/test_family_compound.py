"""Characterization tests for db/families/family_compound.py.

Purpose: guard the refactor only. Compound families change in the db all the
time, so both the inputs and the expected outputs are frozen in the fixture file
and the functions are fed plain attribute holders (SimpleNamespace) — the test
never touches the live db, so it cannot drift when the data changes. It asserts
the refactored code produces byte-identical results for all three pure functions.

The real-data sample covers: passing headwords (comp grammar + short lemma +
meaning_1), multi-member families, a non-comp headword, and a headword with empty
meaning_1 that shares a family with a passing one (exercises the membership guard
in compile_cf_html).
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from db.families.family_compound import (
    compile_cf_html,
    create_comp_fam_dict,
    make_anki_data,
)

FIXTURE_PATH = Path(__file__).parent / "test_family_compound_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _stubs(fixtures: dict) -> list[SimpleNamespace]:
    return [SimpleNamespace(**row) for row in fixtures["inputs"]]


def _norm(obj: object) -> object:
    """Round-trip through json so tuples compare equal to fixture lists."""
    return json.loads(json.dumps(obj, ensure_ascii=False))


def test_create_comp_fam_dict_groups_headwords(fixtures: dict) -> None:
    cf_dict = create_comp_fam_dict(_stubs(fixtures))

    expected_headwords = {
        fam: data["headwords"] for fam, data in fixtures["expected_dict"].items()
    }
    actual_headwords = {fam: data["headwords"] for fam, data in cf_dict.items()}
    assert actual_headwords == expected_headwords

    for data in cf_dict.values():
        assert data["html"] == ""
        assert data["data"] == []
        assert data["anki"] == []


def test_compile_cf_html(fixtures: dict) -> None:
    stubs = _stubs(fixtures)
    cf_dict = create_comp_fam_dict(stubs)
    cf_dict = compile_cf_html(stubs, cf_dict)

    assert _norm(cf_dict) == fixtures["expected_dict"]


def test_make_anki_data(fixtures: dict) -> None:
    stubs = _stubs(fixtures)
    cf_dict = create_comp_fam_dict(stubs)
    cf_dict = compile_cf_html(stubs, cf_dict)
    anki = make_anki_data(cf_dict)

    assert _norm(anki) == fixtures["expected_anki"]
