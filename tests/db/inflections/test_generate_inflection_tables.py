"""Tests for db/inflections/generate_inflection_tables.py

Fixtures in generate_inflection_tables_fixtures.json were captured from the
current code before any refactoring and represent approved output. Tests assert
that generate_inflection_table() produces byte-identical results so a refactor
cannot silently change the HTML or inflection list.

Coverage:
    - normal declension, non-irreg (akakkasa)
    - normal conjugation, non-irreg (akaḍḍhi)
    - irreg conjugation with ! in stem (akaramha)
    - irreg declension (akaci 1)
    - None template short-circuit
    - process_inflection branching: no flags, changed headword, changed template,
      regenerate_all, ! stem, empty pattern (indeclinable)
"""

import json
from pathlib import Path

import pytest

from db.db_helpers import get_db_session
from db.inflections.generate_inflection_tables import InflectionsManager
from db.models import DpdHeadword

FIXTURE_PATH = Path(__file__).parent / "generate_inflection_tables_fixtures.json"
DB_PATH = Path("dpd.db")


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def db():
    return get_db_session(DB_PATH)


def make_manager(tipitaka_words: set[str] | None = None) -> InflectionsManager:
    """Minimal InflectionsManager with only the attributes generate_inflection_table needs."""
    m = object.__new__(InflectionsManager)
    m.all_tipitaka_words = tipitaka_words or set()
    m.inflections_html = ""
    m.inflections_list = []
    m.changed_headwords = []
    m.changed_templates = []
    m.regenerate_all = False
    m.updated_counter = 0
    return m


# ---------------------------------------------------------------------------
# generate_inflection_table — full output matches frozen fixtures
# ---------------------------------------------------------------------------


def test_normal_declension_non_irreg(db, fixtures) -> None:
    """akakkasa: declension, non-irreg, one word in tipitaka set → full match."""
    case = fixtures["akakkasa"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma"]).first()
    m = make_manager(tipitaka_words=set(case["tipitaka_words"]))
    m.generate_inflection_table(hw)
    assert m.inflections_html == case["inflections_html"]
    assert m.inflections_list == case["inflections_list"]


def test_normal_conjugation_non_irreg(db, fixtures) -> None:
    """akaḍḍhi: conjugation, non-irreg, empty tipitaka set → full match."""
    case = fixtures["akaḍḍhi"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma"]).first()
    m = make_manager()
    m.generate_inflection_table(hw)
    assert m.inflections_html == case["inflections_html"]
    assert m.inflections_list == case["inflections_list"]


def test_irreg_conjugation_exclamation_stem(db, fixtures) -> None:
    """akaramha: irreg conjugation, ! in stem → full match."""
    case = fixtures["akaramha"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma"]).first()
    m = make_manager()
    m.generate_inflection_table(hw)
    assert m.inflections_html == case["inflections_html"]
    assert m.inflections_list == case["inflections_list"]


def test_irreg_declension(db, fixtures) -> None:
    """akaci 1: irreg declension → full match."""
    case = fixtures["akaci_1"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma"]).first()
    m = make_manager()
    m.generate_inflection_table(hw)
    assert m.inflections_html == case["inflections_html"]
    assert m.inflections_list == case["inflections_list"]


def test_none_template_short_circuits(db) -> None:
    """Headword whose .it is None → empty html and list, no error."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    original_it = hw.it
    hw.it = None
    m = make_manager()
    m.generate_inflection_table(hw)
    hw.it = original_it  # restore so other tests are unaffected
    assert m.inflections_html == ""
    assert m.inflections_list == []


# ---------------------------------------------------------------------------
# Tipitaka membership — word in set gets bold, word absent gets gray span
# ---------------------------------------------------------------------------


def test_tipitaka_word_rendered_bold(db) -> None:
    """A word present in the tipitaka set is rendered without gray span."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager(tipitaka_words={"akakkaso"})
    m.generate_inflection_table(hw)
    assert "akakkas<b>o</b>" in m.inflections_html
    assert "<span class='gray'>akakkas<b>o</b></span>" not in m.inflections_html


def test_tipitaka_absent_word_rendered_gray(db) -> None:
    """A word absent from the tipitaka set is wrapped in gray span."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager(tipitaka_words=set())
    m.generate_inflection_table(hw)
    assert "<span class='gray'>akakkas<b>o</b></span>" in m.inflections_html


# ---------------------------------------------------------------------------
# process_inflection — branching logic
# ---------------------------------------------------------------------------


def test_process_inflection_no_flags_skips(db) -> None:
    """No flag set → headword not processed, counter unchanged."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager()
    m.process_inflection(hw)
    assert m.updated_counter == 0


def test_process_inflection_changed_headword_triggers(db) -> None:
    """Headword in changed_headwords → processed, counter incremented."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager()
    m.changed_headwords = [hw.lemma_1]
    m.process_inflection(hw)
    assert m.updated_counter == 1
    assert m.inflections_html != ""
    assert hw.lemma_clean in m.inflections_list


def test_process_inflection_changed_template_triggers(db) -> None:
    """Pattern in changed_templates → processed, counter incremented."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager()
    m.changed_templates = [hw.pattern]
    m.process_inflection(hw)
    assert m.updated_counter == 1


def test_process_inflection_regenerate_all_triggers(db) -> None:
    """regenerate_all=True → processed regardless of other flags."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akakkasa").first()
    m = make_manager()
    m.regenerate_all = True
    m.process_inflection(hw)
    assert m.updated_counter == 1


def test_process_inflection_exclamation_stem_sets_lemma_clean_only(db) -> None:
    """! in stem → inflections = lemma_clean only, html table still generated."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="akaramha").first()
    assert "!" in hw.stem
    m = make_manager()
    m.regenerate_all = True
    m.process_inflection(hw)
    assert hw.inflections == hw.lemma_clean
    assert hw.inflections_html != ""


def test_process_inflection_indeclinable_sets_lemma_clean_only(db) -> None:
    """Empty pattern (indeclinable) → inflections = lemma_clean, no html table."""
    hw = db.query(DpdHeadword).filter_by(lemma_1="a 1.1").first()
    assert hw.pattern == ""
    m = make_manager()
    m.regenerate_all = True
    m.process_inflection(hw)
    assert hw.inflections == hw.lemma_clean
