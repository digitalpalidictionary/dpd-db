"""DB related functions:
1. Create db if doesn't already exist,
2. Create db Session
3. Get column names,
4. Print column names.
"""

import os
import sys
import threading
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, func, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from db.models import Base, DpdHeadword
from tools.printer import printer as pr

_engine_cache: dict[Path, Engine] = {}
_engine_cache_lock = threading.Lock()
_engine_cache_pid: int = os.getpid()


def create_db_if_not_exists(db_path: Path):
    """Create the db if it does not exist already."""
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    if not db_path.is_file():
        Base.metadata.create_all(bind=engine)


def create_tables(db_path: Path):
    """Create tables if they don't exist."""
    engine = create_engine(f"sqlite+pysqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)


def _get_cached_engine(db_path: Path) -> Engine:
    """One Engine (with its connection pool and WAL listener) per db file
    per process. Creating an Engine per session leaks file descriptors —
    nothing ever disposes them — and costs ~14x more than reusing one.
    """
    global _engine_cache_pid
    resolved = db_path.resolve()
    with _engine_cache_lock:
        # A forked child inherits this cache but must never reuse the
        # parent's pooled connections (shared SQLite fds across processes
        # corrupt the db). Drop the cache without dispose() — the pooled
        # fds still belong to the parent.
        if os.getpid() != _engine_cache_pid:
            _engine_cache.clear()
            _engine_cache_pid = os.getpid()

        engine = _engine_cache.get(resolved)
        if engine is None:
            engine = create_engine(
                f"sqlite+pysqlite:///{resolved}",
                echo=False,
                # NullPool, not the default QueuePool: gui2 keeps many
                # long-lived sessions that hold their connection for the
                # session's whole life, so a bounded shared pool exhausts
                # ("QueuePool limit of size 5 overflow 10 reached") and
                # 30s-blocks unrelated queries. SQLite connections are
                # cheap to open; pooling buys nothing here.
                poolclass=NullPool,
                # Flet runs event handlers in a thread pool; disabling this
                # check allows cross-thread use. Session is still not
                # thread-safe — if flaky transaction errors appear, migrate
                # GUI to scoped_session.
                connect_args={"check_same_thread": False},
            )

            @event.listens_for(engine, "connect")
            def set_wal_mode(dbapi_conn, _):
                dbapi_conn.execute("PRAGMA journal_mode=WAL")

            _engine_cache[resolved] = engine
    return engine


def get_db_session(db_path: Path) -> Session:
    """Get the db session, used ubiquitously."""
    if not os.path.isfile(db_path):
        pr.red(f"Database file doesn't exist: {db_path}")
        sys.exit(1)

    try:
        return Session(bind=_get_cached_engine(db_path))
    except Exception as e:
        pr.red(f"Can't connect to database: {e}")
        sys.exit(1)


def print_column_names(tables_name):
    """Print a numbered list of all the column names in a given table."""

    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    for counter, column_name in enumerate(column_names):
        print(f"{counter}. {column_name}")


def get_column_names(tables_name):
    inspector = inspect(tables_name)
    column_names = [column.name for column in inspector.columns]
    return column_names


def make_roots_count_dict(db_session: Session) -> dict[str, int]:
    """Count headwords per root_key with a single SQL aggregation."""
    rows = (
        db_session.query(DpdHeadword.root_key, func.count())
        .filter(DpdHeadword.root_key.is_not(None))
        .group_by(DpdHeadword.root_key)
        .all()
    )
    return {root_key: count for root_key, count in rows}
