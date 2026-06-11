"""Parity tests for exporter/webapp/preloads.py make_roots_count_dict.

Locks the webapp's roots count against the same frozen fixture as the
goldendict implementation, proving the two stay interchangeable.
"""

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models import Base, DpdHeadword
from exporter.goldendict.helpers import make_roots_count_dict as goldendict_make
from exporter.webapp.preloads import make_roots_count_dict as webapp_make

FIXTURE_PATH = (
    Path(__file__).parent.parent / "goldendict" / "test_helpers_fixtures.json"
)
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


def test_webapp_roots_count_matches_frozen_output() -> None:
    session = _build_session()
    assert webapp_make(session) == FIXTURE["expected"]


def test_webapp_roots_count_matches_goldendict() -> None:
    session = _build_session()
    assert webapp_make(session) == goldendict_make(session)


def test_webapp_roots_count_empty_db() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    assert webapp_make(session) == {}
