"""Tests for scripts/build/root_has_verb_updater.py

Fixtures were captured from the current code against dpd.db before any
refactoring. Tests assert byte-identical output so a refactor cannot silently
change which roots are marked as having verbs.

Coverage:
    test_root_has_verb  — True (verbal pos, no deno), False (non-verbal pos),
                          False (deno in grammar)
    make_root_has_verb_dict — spot-checks known roots against DB-confirmed values
                              and verifies the full dict covers all roots
"""

import json
from pathlib import Path

import pytest

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from scripts.build.root_has_verb_updater import RootHasVerbUpdater

FIXTURE_PATH = Path(__file__).parent / "root_has_verb_updater_fixtures.json"
DB_PATH = Path("dpd.db")


@pytest.fixture(scope="module")
def fixtures() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def db():
    return get_db_session(DB_PATH)


def make_updater() -> RootHasVerbUpdater:
    """Minimal RootHasVerbUpdater with only the attributes the methods need."""
    u = object.__new__(RootHasVerbUpdater)
    u.verbs = ["pr", "aor", "perf", "imperf", "inf", "abs", "prp", "pp", "ptp"]
    u.verb_yes = "･"
    u.verb_no = "×"
    return u


# ---------------------------------------------------------------------------
# test_root_has_verb
# ---------------------------------------------------------------------------


def test_root_has_verb_returns_true_for_verbal_pos(db, fixtures) -> None:
    """A headword with verbal pos and no deno → True."""
    case = fixtures["test_root_has_verb"]["verb_headword"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma_1"]).first()
    u = make_updater()
    assert u.test_root_has_verb(hw) is True


def test_root_has_verb_returns_false_for_non_verbal_pos(db, fixtures) -> None:
    """A headword with non-verbal pos → False."""
    case = fixtures["test_root_has_verb"]["non_verb_headword"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma_1"]).first()
    u = make_updater()
    assert u.test_root_has_verb(hw) is False


def test_root_has_verb_returns_false_when_deno_in_grammar(db, fixtures) -> None:
    """A headword with verbal pos but deno in grammar → False."""
    case = fixtures["test_root_has_verb"]["deno_grammar_headword"]
    hw = db.query(DpdHeadword).filter_by(lemma_1=case["lemma_1"]).first()
    u = make_updater()
    assert u.test_root_has_verb(hw) is False


# ---------------------------------------------------------------------------
# make_root_has_verb_dict
# ---------------------------------------------------------------------------


def test_make_root_has_verb_dict_spot_checks(db, fixtures) -> None:
    """Known roots match DB-confirmed verb_yes / verb_no values."""
    u = make_updater()
    u.dpd_db = (
        db.query(DpdHeadword)
        .filter(DpdHeadword.root_key != "")
        .order_by(DpdHeadword.root_key)
        .all()
    )
    u.root_has_verb_dict = {}
    u.make_root_has_verb_dict()

    expected = fixtures["make_root_has_verb_dict"]
    for root, value in expected.items():
        assert u.root_has_verb_dict[root] == value, (
            f"{root}: expected {value!r}, got {u.root_has_verb_dict[root]!r}"
        )


def test_make_root_has_verb_dict_covers_all_roots(db, fixtures) -> None:
    """Dict size matches the number of distinct root keys in the DB."""
    u = make_updater()
    u.dpd_db = (
        db.query(DpdHeadword)
        .filter(DpdHeadword.root_key != "")
        .order_by(DpdHeadword.root_key)
        .all()
    )
    u.root_has_verb_dict = {}
    u.make_root_has_verb_dict()

    assert len(u.root_has_verb_dict) == fixtures["full_dict_size"]
