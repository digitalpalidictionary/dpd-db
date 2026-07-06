"""Tests for tools/deconstructed_words.make_words_in_deconstructions.

Runs against an in-memory SQLite db with the real Lookup model (no mocks),
following the tests/tools/test_lookup_sync.py pattern. Pins the single-column
query contract: only Lookup.deconstructor is read, output is the set of
every word appearing in any deconstruction split.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Lookup
from tools.deconstructed_words import make_words_in_deconstructions


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _add(session: Session, lookup_key: str, deconstructions: list[str]) -> None:
    row = Lookup(lookup_key=lookup_key)
    row.deconstructor_pack(deconstructions)
    session.add(row)
    session.commit()


def test_collects_words_from_all_deconstruction_splits(db_session: Session) -> None:
    _add(db_session, "akataṃpi", ["a + kataṃ + pi"])
    _add(db_session, "dhammassa", ["dhamma + assa"])

    result = make_words_in_deconstructions(db_session)

    assert result == {"a", "kataṃ", "pi", "dhamma", "assa"}


def test_ignores_rows_with_no_deconstructor(db_session: Session) -> None:
    _add(db_session, "akataṃpi", ["a + kataṃ + pi"])
    row = Lookup(lookup_key="plain")
    db_session.add(row)
    db_session.commit()

    result = make_words_in_deconstructions(db_session)

    assert result == {"a", "kataṃ", "pi"}


def test_empty_table_returns_empty_set(db_session: Session) -> None:
    assert make_words_in_deconstructions(db_session) == set()
