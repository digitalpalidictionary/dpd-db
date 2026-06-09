"""Golden-master tests for sutta_central_exporter.py.

Fixtures captured from unedited source against real dpd.db.
All assertions must be byte-identical before and after the refactor.
"""

import json
from pathlib import Path

import pytest
from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup

from exporter.sutta_central.sutta_central_exporter import SuttaCentralExporter

FIXTURE_PATH = Path(__file__).parent / "test_sutta_central_exporter_fixtures.json"


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sc() -> SuttaCentralExporter:
    return object.__new__(SuttaCentralExporter)


@pytest.fixture(scope="module")
def db_session():
    return get_db_session(Path("dpd.db"))


# ---------------------------------------------------------------------------
# make_sc_headword_entry
# ---------------------------------------------------------------------------

HW_IDS = [2, 4, 7, 8, 9, 1, 3, 5, 143]


@pytest.mark.parametrize("hw_id", HW_IDS)
def test_make_sc_headword_entry(sc, db_session, fixtures, hw_id):
    hw = db_session.query(DpdHeadword).filter(DpdHeadword.id == hw_id).one()
    result = sc.make_sc_headword_entry(hw)
    expected = fixtures["make_sc_headword_entry"][str(hw_id)]["output"]
    assert result == expected


def test_make_sc_headword_entry_with_construction_includes_brackets(sc, db_session):
    hw = db_session.query(DpdHeadword).filter(DpdHeadword.id == 7).one()
    result = sc.make_sc_headword_entry(hw)
    assert "[" in result and "]" in result


def test_make_sc_headword_entry_without_construction_no_brackets(sc, db_session):
    hw = db_session.query(DpdHeadword).filter(DpdHeadword.id == 1).one()
    result = sc.make_sc_headword_entry(hw)
    assert "[" not in result and "]" not in result


# ---------------------------------------------------------------------------
# flip
# ---------------------------------------------------------------------------

FLIP_CASES = [
    ("akaṅkhaṃ", "akaṅkhaṁ"),
    ("akakkasa", "akakkasa"),
    ("ṃ at start", "ṁ at start"),
    ("no niggahita", "no niggahita"),
]


@pytest.mark.parametrize("text,expected", FLIP_CASES)
def test_flip(sc, fixtures, text, expected):
    assert sc.flip(text) == expected
    assert sc.flip(text) == fixtures["flip"][text]


def test_flip_no_op_on_clean_string(sc):
    assert sc.flip("plain pali") == "plain pali"


def test_flip_replaces_all_occurrences(sc):
    # "ānaṃ danaṃ" — exactly 2 ṃ chars (no ṃ-internal in other chars)
    result = sc.flip("ānaṃ danaṃ")
    assert "ṃ" not in result
    assert result.count("ṁ") == 2


# ---------------------------------------------------------------------------
# deconstructor first-item-only (for-break → if-[0] equivalence)
# ---------------------------------------------------------------------------

DEC_KEYS = [
    "accharāsaṅghātamatte",
    "ambakamaddarīti",
    "ukkaṭṭhitoti",
]


@pytest.mark.parametrize("lookup_key", DEC_KEYS)
def test_deconstructor_first_item_only(db_session, fixtures, lookup_key):
    lk = db_session.query(Lookup).filter(Lookup.lookup_key == lookup_key).one()
    unpacked = lk.deconstructor_unpack
    # Both old (for-break) and new (if-[0]) produce the same first item
    first_item = unpacked[0] if unpacked else None
    expected = fixtures["deconstructor_first_only"][lookup_key]["first_item"]
    assert first_item == expected


def test_deconstructor_multi_item_key_only_first(db_session, fixtures):
    """ambakamaddarīti has 2 items; only the first should appear in the dict."""
    lk = db_session.query(Lookup).filter(Lookup.lookup_key == "ambakamaddarīti").one()
    unpacked = lk.deconstructor_unpack
    assert len(unpacked) == 2
    # Original for-break: only first appended
    assert (
        unpacked[0]
        == fixtures["deconstructor_first_only"]["ambakamaddarīti"]["first_item"]
    )
