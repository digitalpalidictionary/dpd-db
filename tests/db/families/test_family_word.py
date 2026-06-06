"""Characterization tests for db/families/family_word.py.

Purpose: guard the refactor only. Word families change in the db all the time,
so both the inputs and the expected outputs are frozen in the fixture file and
the functions are fed plain attribute holders (SimpleNamespace) — the test never
touches the live db, so it cannot drift when the data changes. It asserts the
refactored code produces byte-identical results for the preserved outputs
("headwords", "html", "data" and the anki html). The dead "anki" working key is
intentionally dropped by the refactor, so it is stripped before comparison.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from db.families.family_word import (
    compile_wf_html,
    make_anki_data,
    make_word_fam_dict,
)

FIXTURE_PATH = Path(__file__).parent / "test_family_word_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _stubs(fixtures: dict) -> list[SimpleNamespace]:
    return [SimpleNamespace(**row) for row in fixtures["inputs"]]


def _norm(obj: object) -> object:
    """Round-trip through json so tuples compare equal to fixture lists."""
    return json.loads(json.dumps(obj, ensure_ascii=False))


def _strip_anki(wf_dict: dict) -> dict:
    return {
        fam: {k: v for k, v in data.items() if k != "anki"}
        for fam, data in wf_dict.items()
    }


def test_make_word_fam_dict_groups_headwords(fixtures: dict) -> None:
    wf_dict = make_word_fam_dict(_stubs(fixtures))

    expected_headwords = {
        fam: data["headwords"] for fam, data in fixtures["expected_dict"].items()
    }
    actual_headwords = {fam: data["headwords"] for fam, data in wf_dict.items()}
    assert actual_headwords == expected_headwords

    for data in wf_dict.values():
        assert data["html"] == ""
        assert data["data"] == []


def test_compile_wf_html(fixtures: dict) -> None:
    stubs = _stubs(fixtures)
    wf_dict = make_word_fam_dict(stubs)
    wf_dict = compile_wf_html(stubs, wf_dict)

    assert _norm(_strip_anki(wf_dict)) == fixtures["expected_dict"]


def test_make_anki_data(fixtures: dict) -> None:
    stubs = _stubs(fixtures)
    wf_dict = make_word_fam_dict(stubs)
    wf_dict = compile_wf_html(stubs, wf_dict)
    anki = make_anki_data(wf_dict)

    assert _norm(anki) == fixtures["expected_anki"]
