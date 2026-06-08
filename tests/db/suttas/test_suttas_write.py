"""Behavioural tests for db/suttas/suttas_to_lookup.py::add_to_lookup_table.

Uses an in-memory SQLite db with the real Lookup model — no mocks.
Verifies the three critical properties of the clear_stale=False write path:
  1. an existing sutta-code row is updated
  2. a new sutta code is inserted
  3. an existing inflection headwords row (key NOT in sutta_data) is left untouched
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Lookup
from tools.lookup_sync import sync_lookup_column


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _get(session: Session, key: str) -> Lookup | None:
    return session.query(Lookup).filter(Lookup.lookup_key == key).first()


def test_existing_sutta_code_is_updated(db_session: Session) -> None:
    """An existing sutta-code headwords row gets the new id list."""
    row = Lookup()
    row.lookup_key = "MN1"
    row.headwords_pack([100])
    db_session.add(row)
    db_session.commit()

    data = {"MN1": [200]}
    sync_lookup_column(db_session, "headwords", data, clear_stale=False)

    refreshed = _get(db_session, "MN1")
    assert refreshed is not None
    assert refreshed.headwords_unpack == [200]


def test_new_sutta_code_is_inserted(db_session: Session) -> None:
    """A sutta code not yet in the table is inserted."""
    data = {"DN2": [42]}
    result = sync_lookup_column(db_session, "headwords", data, clear_stale=False)

    row = _get(db_session, "DN2")
    assert row is not None
    assert row.headwords_unpack == [42]
    assert result.inserted == 1


def test_inflection_headwords_row_is_left_untouched(db_session: Session) -> None:
    """An inflection row (key not in sutta_data) must survive clear_stale=False."""
    inflection_row = Lookup()
    inflection_row.lookup_key = "karoti"
    inflection_row.headwords_pack([999])
    db_session.add(inflection_row)
    db_session.commit()

    data = {"MN1": [100]}
    sync_lookup_column(db_session, "headwords", data, clear_stale=False)

    kept = _get(db_session, "karoti")
    assert kept is not None
    assert kept.headwords_unpack == [999]


def test_sutta_and_inflection_rows_coexist_after_sync(db_session: Session) -> None:
    """Combined scenario: update sutta, insert sutta, leave inflection row alone."""
    existing_sutta = Lookup()
    existing_sutta.lookup_key = "SN1.1"
    existing_sutta.headwords_pack([10])

    inflection = Lookup()
    inflection.lookup_key = "gacchati"
    inflection.headwords_pack([555])

    db_session.add_all([existing_sutta, inflection])
    db_session.commit()

    data = {"SN1.1": [20], "AN3.1": [30]}
    result = sync_lookup_column(db_session, "headwords", data, clear_stale=False)

    assert _get(db_session, "SN1.1").headwords_unpack == [20]  # type: ignore[union-attr]
    assert _get(db_session, "AN3.1").headwords_unpack == [30]  # type: ignore[union-attr]
    assert _get(db_session, "gacchati").headwords_unpack == [555]  # type: ignore[union-attr]
    assert (result.updated, result.inserted, result.cleared, result.deleted) == (
        1,
        1,
        0,
        0,
    )
