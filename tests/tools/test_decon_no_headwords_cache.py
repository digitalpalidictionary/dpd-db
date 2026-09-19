# -*- coding: utf-8 -*-
"""Behavioural tests for the all_decon_no_headwords DbInfo cache.

Runs against an in-memory SQLite db with the real models (no mocks),
following the tests/tools/test_lookup_sync.py pattern.
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DbInfo
from tools.cache_load import (
    DECON_NO_HEADWORDS_CACHE_KEY,
    invalidate_decon_no_headwords_cache,
    load_decon_no_headwords_cache,
    save_decon_no_headwords_cache,
)
from tools.lookup_sync import sync_lookup_column


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def test_absent_cache_returns_none(db_session: Session) -> None:
    assert load_decon_no_headwords_cache(db_session) is None


def test_save_load_round_trip(db_session: Session) -> None:
    save_decon_no_headwords_cache(db_session, {"akāri", "akasi"})
    loaded = load_decon_no_headwords_cache(db_session)
    assert loaded == {"akāri", "akasi"}


def test_save_overwrites_existing_cache(db_session: Session) -> None:
    save_decon_no_headwords_cache(db_session, {"one"})
    save_decon_no_headwords_cache(db_session, {"two"})
    assert load_decon_no_headwords_cache(db_session) == {"two"}
    rows = db_session.query(DbInfo).filter_by(key=DECON_NO_HEADWORDS_CACHE_KEY).all()
    assert len(rows) == 1


def test_corrupt_cache_returns_none(db_session: Session) -> None:
    save_decon_no_headwords_cache(db_session, {"one"})
    row = db_session.query(DbInfo).filter_by(key=DECON_NO_HEADWORDS_CACHE_KEY).one()
    row.value = "{{{ not json"
    db_session.commit()
    assert load_decon_no_headwords_cache(db_session) is None


def test_invalidate_removes_cache(db_session: Session) -> None:
    save_decon_no_headwords_cache(db_session, {"one"})
    invalidate_decon_no_headwords_cache(db_session)
    assert load_decon_no_headwords_cache(db_session) is None


@pytest.fixture(params=[False, True], ids=["orm", "raw_sql"])
def use_raw_sql(request: pytest.FixtureRequest) -> bool:
    return request.param


@pytest.mark.parametrize("column", ["headwords", "deconstructor"])
def test_relevant_lookup_sync_invalidates_cache(
    db_session: Session, column: str, use_raw_sql: bool
) -> None:
    save_decon_no_headwords_cache(db_session, {"one"})
    sync_lookup_column(
        db_session,
        column,
        {"hoti": ["hoti 1"]},
        clear_stale=False,
        use_raw_sql=use_raw_sql,
    )
    assert load_decon_no_headwords_cache(db_session) is None


@pytest.mark.parametrize("column", ["see", "spelling", "grammar"])
def test_unrelated_lookup_sync_keeps_cache(db_session: Session, column: str) -> None:
    save_decon_no_headwords_cache(db_session, {"one"})
    sync_lookup_column(db_session, column, {"hoti": "see hoti"}, clear_stale=False)
    assert load_decon_no_headwords_cache(db_session) == {"one"}
