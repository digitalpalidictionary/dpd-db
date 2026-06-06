"""Characterization tests for db/families/family_set.py.

Guards the refactor only. Inputs and expected outputs are frozen in the fixture
file; stubs are plain SimpleNamespace objects so the test never touches the live
db. Covers all four sort strategies (natsort prefix, bracket_number, day_order,
default Pāḷi) and the meaning_1-empty exclusion path.
"""

import json
from pathlib import Path
from types import SimpleNamespace

from db.families.family_set import compile_sf_html, make_sets_dict

FIXTURE_PATH = Path(__file__).parent / "test_family_set_fixtures.json"


def _fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _stubs(fixtures: dict) -> list[SimpleNamespace]:
    return [SimpleNamespace(**row) for row in fixtures["inputs"]]


def _norm(obj: object) -> object:
    """Round-trip through JSON so tuples compare equal to fixture lists."""
    return json.loads(json.dumps(obj, ensure_ascii=False))


def test_make_sets_dict_groups_headwords() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    sd = make_sets_dict(stubs)

    expected_headwords = {
        sf: data["headwords"] for sf, data in fixtures["expected_dict"].items()
    }
    actual_headwords = {sf: data["headwords"] for sf, data in sd.items()}
    assert actual_headwords == expected_headwords

    for data in sd.values():
        assert data["html"] == ""
        assert data["data"] == []


def test_make_sets_dict_excludes_empty_meaning_1() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    sd = make_sets_dict(stubs)

    # kassapasammāsambuddha has meaning_1=False — must not appear in any headword list
    for sf, data in sd.items():
        assert "kassapasammāsambuddha" not in data["headwords"], (
            f"headword with empty meaning_1 should be excluded from set '{sf}'"
        )


def test_compile_sf_html_all_sets_byte_identical() -> None:
    fixtures = _fixtures()
    stubs = _stubs(fixtures)

    sd = make_sets_dict(stubs)
    sd = compile_sf_html(stubs, sd)

    serializable = {
        sf: {
            "headwords": v["headwords"],
            "html": v["html"],
            "data": [list(t) for t in v["data"]],
        }
        for sf, v in sd.items()
    }
    assert serializable == fixtures["expected_dict"]
