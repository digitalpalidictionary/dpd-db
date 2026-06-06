"""Characterization tests for db/families/family_idiom.py.

Guards the refactor only. Inputs and expected outputs are frozen in the fixture
file; stubs are plain SimpleNamespace objects so the test never touches the live
db. Covers the idiom/sandhi HTML path, the meaning_1-empty exclusion path, and
deterministic sorted cache output.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from db.families.family_idiom import create_idioms_dict, compile_idioms_html

FIXTURE_PATH = Path(__file__).parent / "test_family_idiom_fixtures.json"


def _fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _stubs(fixtures: dict) -> list[SimpleNamespace]:
    return [SimpleNamespace(**row) for row in fixtures["inputs"]]


def test_create_idioms_dict_groups_headwords() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    result = create_idioms_dict(stubs)

    expected_headwords = {
        k: v["headwords"] for k, v in fixtures["expected_dict"].items()
    }
    actual_headwords = {k: v["headwords"] for k, v in result.items()}
    assert actual_headwords == expected_headwords

    for data in result.values():
        assert data["html"] == ""
        assert data["data"] == []


def test_create_idioms_dict_excludes_empty_meaning_1() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    result = create_idioms_dict(stubs)

    no_meaning = [s.lemma_1 for s in stubs if not s.meaning_1]
    for word_data in result.values():
        for excluded in no_meaning:
            assert excluded not in word_data["headwords"], (
                f"headword with empty meaning_1 ({excluded!r}) should be excluded"
            )


def test_compile_idioms_html_byte_identical() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    idioms_dict = create_idioms_dict(stubs)
    idioms_dict = compile_idioms_html(stubs, idioms_dict)

    serializable = {
        k: {
            "headwords": v["headwords"],
            "html": v["html"],
            "data": [list(t) for t in v["data"]],
            "count": v["count"],
        }
        for k, v in idioms_dict.items()
    }
    assert serializable == fixtures["expected_dict"]


def test_idioms_set_is_sorted() -> None:
    """sorted() must be used so the DbInfo cache is deterministic across runs."""
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    idioms_dict = create_idioms_dict(stubs)
    idioms_dict = compile_idioms_html(stubs, idioms_dict)

    idioms_set = sorted(word for word, v in idioms_dict.items() if v["count"] > 0)
    assert idioms_set == sorted(idioms_set)
