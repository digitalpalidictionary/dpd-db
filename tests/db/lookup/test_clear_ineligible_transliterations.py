"""Behavioural tests for the transliteration clearing pass.

Runs against an in-memory SQLite db with the real Lookup model, following the
tests/tools/test_lookup_sync.py pattern.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.lookup.transliterate_lookup_table import _clear_ineligible_transliterations
from db.models import Base, Lookup


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _add(session: Session, key: str, **columns: str) -> None:
    row = Lookup()
    row.lookup_key = key
    for name, value in columns.items():
        setattr(row, name, value)
    session.add(row)
    session.commit()


def _get(session: Session, key: str) -> Lookup:
    row = session.query(Lookup).filter(Lookup.lookup_key == key).first()
    assert row is not None
    return row


def test_epd_only_row_has_its_transliterations_cleared(db_session: Session) -> None:
    _add(
        db_session,
        "un-",
        epd='[["a", "prefix", "not"]]',
        sinhala='["උන්-"]',
        devanagari='["उन्-"]',
        thai='["อุนฺ-"]',
    )

    assert _clear_ineligible_transliterations(db_session) == (1, 0)

    row = _get(db_session, "un-")
    assert (row.sinhala, row.devanagari, row.thai) == ("", "", "")
    assert row.epd == '[["a", "prefix", "not"]]'


def test_row_with_real_content_keeps_its_transliterations(db_session: Session) -> None:
    _add(
        db_session,
        "buddho",
        headwords="[274]",
        epd='[["buddha", "masc", "awakened one"]]',
        sinhala='["බුද්ධො"]',
        devanagari='["बुद्धो"]',
        thai='["พุทฺโธ"]',
    )

    assert _clear_ineligible_transliterations(db_session) == (0, 0)

    row = _get(db_session, "buddho")
    assert row.sinhala == '["බුද්ධො"]'


def test_epd_only_row_without_transliterations_is_not_touched(
    db_session: Session,
) -> None:
    _add(db_session, "not", epd='[["na", "ind", "no; not"]]')

    assert _clear_ineligible_transliterations(db_session) == (0, 0)


def test_row_with_only_transliterations_is_deleted_not_blanked(
    db_session: Session,
) -> None:
    """Blanking it would strand a row no stale pass can ever reach again."""
    _add(
        db_session,
        "karohi",
        sinhala='["කරොහි"]',
        devanagari='["करोहि"]',
        thai='["กโรหิ"]',
    )

    assert _clear_ineligible_transliterations(db_session) == (0, 1)
    assert (
        db_session.query(Lookup).filter(Lookup.lookup_key == "karohi").first() is None
    )
