"""Golden-master test for db/inflections/inflections_to_headwords.py.

Freezes the output of ``inflection_to_headwords`` so the dataclass / type-hint
refactor is proven behaviour-preserving. Fixtures were captured from the
unedited code (see test_inflections_to_headwords_fixtures.json).
"""

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from db.inflections.inflections_to_headwords import (
    GlobalVars,
    inflection_to_headwords,
)

FIXTURE_PATH = Path(__file__).parent / "test_inflections_to_headwords_fixtures.json"


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_g(fixture: dict[str, Any]) -> GlobalVars:
    g = object.__new__(GlobalVars)
    g.dpd_db = cast(
        Any,
        [SimpleNamespace(**hw) for hw in fixture["headwords"]],
    )
    g.all_words_set = set(fixture["all_words_set"])
    g.i2h_dict = {}
    g.i2h_dict_tpr = {}
    return g


def test_inflection_to_headwords_matches_fixture() -> None:
    fixture = _load_fixture()
    g = _build_g(fixture)

    inflection_to_headwords(g)

    assert g.i2h_dict == fixture["expected"]["i2h_dict"]
    assert g.i2h_dict_tpr == fixture["expected"]["i2h_dict_tpr"]


def test_inflection_to_headwords_branches() -> None:
    """Each conditional branch in the build loop is exercised by the fixture."""
    fixture = _load_fixture()
    g = _build_g(fixture)

    inflection_to_headwords(g)

    # append branch: one inflection shared by two headwords -> both ids/lemmas
    assert g.i2h_dict["abhidhammo"] == [1, 2]
    assert g.i2h_dict_tpr["abhidhammo"] == ["abhidhamma 1", "abhidhamma 2"]

    # skip-duplicate branch: a repeated inflection within one headword -> single id
    assert g.i2h_dict["dupword"] == [4]

    # filter branch: inflections absent from all_words_set are dropped
    assert "filteredout" not in g.i2h_dict
    assert "iti" not in g.i2h_dict
