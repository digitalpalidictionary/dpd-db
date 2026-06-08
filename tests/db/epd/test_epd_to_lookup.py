"""Characterization tests for db/epd/epd_to_lookup.py.

Fixtures in test_epd_to_lookup_fixtures.json were captured from the pre-refactor
source. The golden-master cases below run identically on the old and new code
(byte-identical refactor). The single new-behaviour case (empty meaning token)
locks the deliberate fix: an empty cleaned token used to create an ``epd_data_dict[""]``
key and is now skipped.
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from db.epd import epd_to_lookup as epd

FIXTURES = json.loads(
    (Path(__file__).parent / "test_epd_to_lookup_fixtures.json").read_text(
        encoding="utf-8"
    )
)


def _make_globals(**attrs: object) -> epd.GlobalVars:
    """Build a GlobalVars without its constructor (works pre- and post-refactor)."""
    g = object.__new__(epd.GlobalVars)
    g.epd_data_dict = {}
    for key, value in attrs.items():
        setattr(g, key, value)
    return g


@pytest.mark.parametrize(
    ("meaning_1", "expected"), list(FIXTURES["make_clean_meaning_list"].items())
)
def test_make_clean_meaning_list(meaning_1: str, expected: list[str]) -> None:
    i = SimpleNamespace(meaning_1=meaning_1)
    assert epd.make_clean_meaning_list(i) == expected


def test_make_meaning_plus_case_no_case() -> None:
    i = SimpleNamespace(meaning_1="to go", plus_case="")
    assert (
        epd.make_meaning_plus_case(i) == FIXTURES["make_meaning_plus_case"]["no_case"]
    )


def test_make_meaning_plus_case_with_case() -> None:
    i = SimpleNamespace(meaning_1="to go", plus_case="instr")
    assert (
        epd.make_meaning_plus_case(i) == FIXTURES["make_meaning_plus_case"]["with_case"]
    )


def test_compile_headwords_data_golden() -> None:
    case = FIXTURES["compile_headwords_data"]
    headwords = [SimpleNamespace(**row) for row in case["inputs"]]
    g = _make_globals(dpd_db=headwords, dpd_db_length=len(headwords))
    epd.compile_headwords_data(g)
    expected = {k: [tuple(t) for t in v] for k, v in case["output"].items()}
    assert g.epd_data_dict == expected


def test_compile_roots_data_golden() -> None:
    case = FIXTURES["compile_roots_data"]
    roots = [SimpleNamespace(**row) for row in case["inputs"]]
    g = _make_globals(roots_db=roots)
    epd.compile_roots_data(g)
    expected = {k: [tuple(t) for t in v] for k, v in case["output"].items()}
    assert g.epd_data_dict == expected


def test_empty_meaning_token_skipped() -> None:
    """A meaning that cleans to '' (e.g. '??') must not create an '' key.

    Unedited source produced epd_data_dict[''] (see the fixture's
    _unedited_empty_token_behaviour: ['']); the refactor skips it.
    """
    headword = SimpleNamespace(
        lemma_clean="dd", pos="noun", meaning_1="??", plus_case="", lemma_1="dd"
    )
    g = _make_globals(dpd_db=[headword], dpd_db_length=1)
    epd.compile_headwords_data(g)
    assert "" not in g.epd_data_dict
    assert g.epd_data_dict == {}
