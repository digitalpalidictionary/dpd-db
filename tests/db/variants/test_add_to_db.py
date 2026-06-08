"""Behavioural tests for AddVariantsToDb.

Drives the real class against an in-memory SQLite db (injected session, real
Lookup model, no mocks). Covers insert / update / stale-clear / stale-delete,
including the case a variant key still present in the data is updated rather than
lost.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, Lookup
from db.variants.add_to_db import AddVariantsToDb

_VARIANT = {"CST": {"text": [["word", "ref"]]}}
_VARIANT_2 = {"CST": {"text": [["other", "ref2"]]}}


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


def test_inserts_new_variant(db_session: Session) -> None:
    AddVariantsToDb({"newkey": _VARIANT}, db_session=db_session)

    row = _get(db_session, "newkey")
    assert row is not None
    assert row.variants_unpack == _VARIANT


def test_updates_existing_variant_not_lost(db_session: Session) -> None:
    """A key present in the data must be updated, never deleted (the bug fix)."""
    existing = Lookup()
    existing.lookup_key = "samekey"
    existing.variants_pack(_VARIANT)
    db_session.add(existing)
    db_session.commit()

    AddVariantsToDb({"samekey": _VARIANT_2}, db_session=db_session)

    row = _get(db_session, "samekey")
    assert row is not None
    assert row.variants_unpack == _VARIANT_2


def test_stale_variant_only_row_is_deleted(db_session: Session) -> None:
    stale = Lookup()
    stale.lookup_key = "stale"
    stale.variants_pack(_VARIANT)
    db_session.add(stale)
    db_session.commit()

    AddVariantsToDb({"keep": _VARIANT}, db_session=db_session)

    assert _get(db_session, "stale") is None
    assert _get(db_session, "keep") is not None


def test_stale_row_with_other_value_is_cleared(db_session: Session) -> None:
    stale = Lookup()
    stale.lookup_key = "shared"
    stale.variants_pack(_VARIANT)
    stale.grammar_pack([["x", "verb", "g"]])
    db_session.add(stale)
    db_session.commit()

    AddVariantsToDb({"keep": _VARIANT}, db_session=db_session)

    row = _get(db_session, "shared")
    assert row is not None
    assert row.variant == ""
    assert row.grammar_unpack == [["x", "verb", "g"]]
