"""Golden-master tests for exporter/goldendict/helpers.py.

Freezes make_roots_count_dict's output (per-root_key headword counts) against a
crafted in-memory db, and locks TODAY to the canonical project clock.
"""

import json
from datetime import date
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, DpdHeadword
from exporter.goldendict.helpers import TODAY, make_roots_count_dict

FIXTURE_PATH = Path(__file__).parent / "test_helpers_fixtures.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(
        DpdHeadword(id=r["id"], lemma_1=r["lemma_1"], root_key=r["root_key"])
        for r in FIXTURE["rows"]
    )
    session.commit()
    return session


def test_make_roots_count_dict_matches_frozen_output() -> None:
    session = _build_session()
    assert make_roots_count_dict(session) == FIXTURE["expected"]


def test_make_roots_count_dict_counts_duplicates_and_empty_key() -> None:
    session = _build_session()
    result = make_roots_count_dict(session)
    assert result["√kar 1"] == 2
    assert result["√gam 1"] == 1
    assert result[""] == 2


def test_make_roots_count_dict_empty_db() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    assert make_roots_count_dict(session) == {}


def test_today_is_a_date() -> None:
    assert isinstance(TODAY, date)
