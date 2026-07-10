# -*- coding: utf-8 -*-
"""Tests for gui2.filter_logic (pure logic extracted from filter_component)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword
from gui2.filter_logic import (
    build_filter_conditions,
    cell_value_str,
    clamp_page_index,
    compute_column_widths,
    effective_total,
    group_changes_by_id,
    page_label,
    parse_id_filter,
    track_cell_change,
    validate_regex_patterns,
)


@pytest.fixture
def db_session() -> Session:  # type: ignore
    """In-memory SQLite session with a few headwords."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    session.add_all(
        [
            DpdHeadword(id=1, lemma_1="kata 1", pos="pp", root_key="√kar"),
            DpdHeadword(id=2, lemma_1="kata 2", pos="adj", root_key="√kar"),
            DpdHeadword(id=3, lemma_1="bhūta 1", pos="pp", root_key="√bhū"),
            DpdHeadword(id=4, lemma_1="dhamma 1", pos="masc", root_key=None),
        ]
    )
    session.commit()
    yield session  # type: ignore
    session.close()


# ── cell_value_str ───────────────────────────────────────────────────────────


def test_cell_value_str_none():
    assert cell_value_str(None) == ""


def test_cell_value_str_list():
    assert cell_value_str(["a", "b", 3]) == "a, b, 3"


def test_cell_value_str_plain():
    assert cell_value_str(42) == "42"
    assert cell_value_str("kata") == "kata"


# ── validate_regex_patterns ──────────────────────────────────────────────────


def test_validate_regex_patterns_all_valid():
    assert validate_regex_patterns([("lemma_1", "^ka"), ("pos", "")]) is None


def test_validate_regex_patterns_invalid_reports_position():
    error = validate_regex_patterns([("lemma_1", "^ka"), ("pos", "(unclosed")])
    assert error is not None
    assert "filter 2" in error


# ── parse_id_filter ──────────────────────────────────────────────────────────


def test_parse_id_filter_valid():
    assert parse_id_filter("^(1571|3106|4365)$") == [1571, 3106, 4365]


def test_parse_id_filter_single_id():
    assert parse_id_filter("^(42)$") == [42]


def test_parse_id_filter_skips_invalid_ids():
    assert parse_id_filter("^(1|abc|3)$") == [1, 3]


def test_parse_id_filter_all_invalid_returns_none():
    assert parse_id_filter("^(abc|def)$") is None


def test_parse_id_filter_wrong_shape_returns_none():
    assert parse_id_filter("^kata$") is None
    assert parse_id_filter("") is None
    assert parse_id_filter("(1|2)") is None


# ── build_filter_conditions ──────────────────────────────────────────────────


def test_build_filter_conditions_unknown_column():
    conditions, error = build_filter_conditions([("no_such_column", "x")])
    assert conditions == []
    assert "no_such_column" in error


def test_build_filter_conditions_id_list_executes(db_session: Session):
    conditions, error = build_filter_conditions([("id", "^(1|3)$")])
    assert error == ""
    rows = db_session.query(DpdHeadword).filter(*conditions).all()
    assert sorted(r.id for r in rows) == [1, 3]


def test_build_filter_conditions_regexp_executes(db_session: Session):
    conditions, error = build_filter_conditions([("lemma_1", "^kata")])
    assert error == ""
    rows = db_session.query(DpdHeadword).filter(*conditions).all()
    assert sorted(r.id for r in rows) == [1, 2]


def test_build_filter_conditions_multiple_filters_and_together(db_session: Session):
    conditions, error = build_filter_conditions([("lemma_1", "1$"), ("pos", "pp")])
    assert error == ""
    rows = db_session.query(DpdHeadword).filter(*conditions).all()
    assert sorted(r.id for r in rows) == [1, 3]


def test_build_filter_conditions_empty_pattern_matches_all(db_session: Session):
    """Empty pattern matches every row, NULL columns included — this is the
    default preset's behavior (all filters empty = whole table)."""
    conditions, error = build_filter_conditions([("root_key", "")])
    assert error == ""
    rows = db_session.query(DpdHeadword).filter(*conditions).all()
    assert sorted(r.id for r in rows) == [1, 2, 3, 4]


# ── compute_column_widths ────────────────────────────────────────────────────


def test_compute_column_widths_empty_results():
    assert compute_column_widths([], ["lemma_1"]) == {}


def test_compute_column_widths_clamps_min(db_session: Session):
    rows = db_session.query(DpdHeadword).all()
    widths = compute_column_widths(rows, ["pos"])
    assert widths["pos"] == 120


def test_compute_column_widths_clamps_max(db_session: Session):
    rows = db_session.query(DpdHeadword).all()
    rows[0].meaning_1 = "x" * 200
    widths = compute_column_widths(rows, ["meaning_1"])
    assert widths["meaning_1"] == 500


def test_compute_column_widths_uses_longest_value(db_session: Session):
    rows = db_session.query(DpdHeadword).all()
    widths = compute_column_widths(rows, ["lemma_1"])
    assert widths["lemma_1"] == max(120, len("dhamma 1") * 8)


# ── track_cell_change ────────────────────────────────────────────────────────


def test_track_cell_change_records_edit():
    modified: dict[tuple[int, str], str] = {}
    track_cell_change(modified, (1, "meaning_1"), "new", "old")
    assert modified == {(1, "meaning_1"): "new"}


def test_track_cell_change_revert_removes_record():
    modified = {(1, "meaning_1"): "new"}
    track_cell_change(modified, (1, "meaning_1"), "old", "old")
    assert modified == {}


def test_track_cell_change_unchanged_untracked_is_noop():
    modified: dict[tuple[int, str], str] = {}
    track_cell_change(modified, (1, "meaning_1"), "same", "same")
    assert modified == {}


# ── group_changes_by_id ──────────────────────────────────────────────────────


def test_group_changes_by_id():
    modified = {
        (1, "meaning_1"): "a",
        (1, "pos"): "b",
        (2, "meaning_1"): "c",
    }
    assert group_changes_by_id(modified) == {
        1: {"meaning_1": "a", "pos": "b"},
        2: {"meaning_1": "c"},
    }


def test_group_changes_by_id_empty():
    assert group_changes_by_id({}) == {}


# ── pagination helpers ───────────────────────────────────────────────────────


def test_effective_total_no_limit():
    assert effective_total(500, 0) == 500


def test_effective_total_with_limit():
    assert effective_total(500, 100) == 100
    assert effective_total(50, 100) == 50


def test_clamp_page_index_within_range():
    assert clamp_page_index(2, 500, 100) == 2


def test_clamp_page_index_past_end():
    assert clamp_page_index(9, 500, 100) == 4
    assert clamp_page_index(1, 100, 100) == 0


def test_clamp_page_index_negative_and_empty():
    assert clamp_page_index(-1, 500, 100) == 0
    assert clamp_page_index(3, 0, 100) == 0


def test_page_label_first_page():
    assert page_label(0, 100, 5432) == "1–100 of 5432"


def test_page_label_last_partial_page():
    assert page_label(54, 100, 5432) == "5401–5432 of 5432"


def test_page_label_empty():
    assert page_label(0, 100, 0) == "0 of 0"
