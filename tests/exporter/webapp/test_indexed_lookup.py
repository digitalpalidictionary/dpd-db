"""Index lifecycle, ASCII matching semantics and mobile export isolation."""

import sqlite3
from pathlib import Path
from typing import cast
from types import SimpleNamespace

import pytest
from sqlalchemy import Table, create_engine

from db.models import Lookup
from exporter.mobile.mobile_exporter import GlobalVars, export_lookup
from tools.prepare_webapp_lookup import prepare_lookup_index


def test_existing_database_and_idempotence(tmp_path: Path) -> None:
    path = tmp_path / "dpd.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE lookup(lookup_key TEXT PRIMARY KEY, headwords TEXT)")
        db.executemany(
            "INSERT INTO lookup VALUES (?, '')",
            [(x,) for x in ["Root", "root", "root.", "rÖot", "%", "_"]],
        )
    prepare_lookup_index(path)
    prepare_lookup_index(path)
    with sqlite3.connect(path) as db:
        for q in ["Root", "ROOT", "röot", "%", "_", "missing", "r\x00oot"]:
            escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            old = db.execute(
                "SELECT * FROM lookup WHERE lower(lookup_key) LIKE lower(?) ESCAPE '\\' OR lower(lookup_key) LIKE lower(?) ESCAPE '\\'",
                (escaped, escaped + "."),
            ).fetchall()
            if "\x00" not in q:
                new = db.execute(
                    "SELECT * FROM lookup WHERE lookup_key COLLATE NOCASE IN (?, ?) ORDER BY rowid",
                    (q, q + "."),
                ).fetchall()
                assert old == new
        assert not db.execute("PRAGMA index_list(lookup)").fetchall()[0][2]


@pytest.mark.parametrize(
    "ddl",
    [
        "CREATE UNIQUE INDEX ix_lookup_key_nocase ON lookup(lookup_key COLLATE NOCASE)",
        "CREATE INDEX ix_lookup_key_nocase ON lookup(lookup_key)",
        "CREATE INDEX ix_lookup_key_nocase ON lookup(lookup_key COLLATE NOCASE) WHERE lookup_key != ''",
        "CREATE INDEX ix_lookup_key_nocase ON lookup(lookup_key COLLATE NOCASE DESC)",
    ],
)
def test_reject_wrong_definition(tmp_path: Path, ddl: str) -> None:
    path = tmp_path / "dpd.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE lookup(lookup_key TEXT)")
        db.execute(ddl)
    with pytest.raises(ValueError, match="incompatible"):
        prepare_lookup_index(path)


def test_reject_nul_keys(tmp_path: Path) -> None:
    path = tmp_path / "dpd.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE lookup(lookup_key TEXT)")
        db.execute("INSERT INTO lookup VALUES (?)", ("a\x00b",))
    with pytest.raises(ValueError, match="NUL"):
        prepare_lookup_index(path)


def test_fresh_model_index() -> None:
    engine = create_engine("sqlite://")
    cast(Table, Lookup.__table__).create(engine)
    with engine.connect() as db:
        assert (
            db.exec_driver_sql(
                "SELECT sql FROM sqlite_master WHERE name='ix_lookup_key_nocase'"
            ).scalar()
            == 'CREATE INDEX ix_lookup_key_nocase ON lookup (lookup_key COLLATE "NOCASE")'
        )


def test_mobile_keeps_other_indexes() -> None:
    src = sqlite3.connect(":memory:")
    src.row_factory = sqlite3.Row
    src.execute("CREATE TABLE lookup(lookup_key TEXT PRIMARY KEY, headwords TEXT)")
    src.execute("INSERT INTO lookup VALUES ('deva','[1]')")
    src.execute(
        "CREATE INDEX ix_lookup_key_nocase ON lookup(lookup_key COLLATE NOCASE)"
    )
    src.execute("CREATE INDEX existing_headwords ON lookup(headwords)")
    dest = sqlite3.connect(":memory:")
    export_lookup(cast(GlobalVars, SimpleNamespace(src=src)), dest)
    names = {row[1] for row in dest.execute("PRAGMA index_list(lookup)")}
    assert "ix_lookup_key_nocase" not in names
    assert {
        "existing_headwords",
        "idx_lookup_fuzzy_key",
        "sqlite_autoindex_lookup_1",
    } <= names
    assert dest.execute("SELECT lookup_key, headwords FROM lookup").fetchall() == [
        ("deva", "[1]")
    ]
    src.close()
    dest.close()


def test_nul_query_uses_legacy_like(monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy import event
    from sqlalchemy.orm import Session

    import exporter.webapp.toolkit as toolkit
    from tools.paths import ProjectPaths

    engine = create_engine("sqlite://")
    cast(Table, Lookup.__table__).create(engine)
    with Session(engine) as db:
        db.add_all([Lookup(lookup_key=key) for key in ["a", "a.", "A"]])
        db.commit()

    def session(path: Path) -> Session:
        return Session(engine)

    monkeypatch.setattr(toolkit, "get_db_session", session)
    loaded: list[str] = []

    def record(target: Lookup, context: object) -> None:
        loaded.append(target.lookup_key)

    event.listen(Lookup, "load", record)
    try:
        toolkit.make_dpd_html("a\x00suffix", ProjectPaths(), None, {}, set(), {})
    finally:
        event.remove(Lookup, "load", record)
    assert loaded == ["a", "A"]
