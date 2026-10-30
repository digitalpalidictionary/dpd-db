from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import db_helpers
from db.db_helpers import get_db_session


@pytest.fixture
def small_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A small WAL db, never dpd.db, with a clean engine cache around it."""
    monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
    monkeypatch.setattr("tools.server_mode.config_read", lambda *_: None)
    path = tmp_path / "small.db"
    db_helpers._engine_cache.clear()
    engine = db_helpers._get_cached_engine(path)
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t (id INTEGER)"))
        conn.execute(text("INSERT INTO t VALUES (1)"))
    db_helpers._engine_cache.clear()
    yield path
    db_helpers._engine_cache.clear()


def test_contributor_server_can_read_but_not_write(
    small_db: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
    session = get_db_session(small_db)

    assert session.execute(text("SELECT id FROM t")).scalar() == 1
    with pytest.raises(OperationalError):
        session.execute(text("INSERT INTO t VALUES (2)"))
        session.commit()
    session.rollback()
    assert session.execute(text("SELECT count(*) FROM t")).scalar() == 1


def test_desktop_can_write(small_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
    monkeypatch.setattr("tools.server_mode.config_read", lambda *_: None)
    session = get_db_session(small_db)

    session.execute(text("INSERT INTO t VALUES (2)"))
    session.commit()

    assert session.execute(text("SELECT count(*) FROM t")).scalar() == 2


def test_failed_decon_cache_save_leaves_the_session_usable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from db.db_helpers import create_tables
    from db.models import DbInfo
    from gui2.database_manager import DatabaseManager

    monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
    path = tmp_path / "decon.db"
    db_helpers._engine_cache.clear()
    create_tables(path)
    manager = DatabaseManager.__new__(DatabaseManager)
    manager.db_session = get_db_session(path)
    try:
        # No cache row, so the live query runs and the cache write is refused.
        manager.get_all_decon_no_headwords()

        assert manager.all_decon_no_headwords == set()
        assert manager.db_session.query(DbInfo).count() == 0
    finally:
        db_helpers._engine_cache.clear()
