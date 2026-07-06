# -*- coding: utf-8 -*-
"""Behavioural tests for tools/lookup_sync.sync_lookup_column.

Runs against an in-memory SQLite db with the real Lookup model (no mocks),
following the tests/gui2/test_roots_db.py pattern.
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


@pytest.fixture(params=[False, True], ids=["orm", "raw_sql"])
def use_raw_sql(request: pytest.FixtureRequest) -> bool:
    return request.param


def _get(session: Session, key: str) -> Lookup | None:
    return session.query(Lookup).filter(Lookup.lookup_key == key).first()


def test_insert_new_key(db_session: Session, use_raw_sql: bool) -> None:
    result = sync_lookup_column(
        db_session, "see", {"karohi": ["karoti"]}, use_raw_sql=use_raw_sql
    )
    row = _get(db_session, "karohi")
    assert row is not None
    assert row.see_unpack == ["karoti"]
    assert (result.inserted, result.updated) == (1, 0)


def test_update_existing_key(db_session: Session, use_raw_sql: bool) -> None:
    existing = Lookup()
    existing.lookup_key = "karohi"
    existing.see_pack(["old"])
    db_session.add(existing)
    db_session.commit()

    result = sync_lookup_column(
        db_session, "see", {"karohi": ["karoti"]}, use_raw_sql=use_raw_sql
    )
    row = _get(db_session, "karohi")
    assert row is not None
    assert row.see_unpack == ["karoti"]
    assert (result.inserted, result.updated) == (0, 1)


def test_update_sets_value_on_row_that_only_had_other_column(
    db_session: Session, use_raw_sql: bool
) -> None:
    """A key that exists with an empty target column is an update, not an insert."""
    existing = Lookup()
    existing.lookup_key = "gaccha"
    existing.grammar_pack([["gacchati", "verb", "pr 3sg"]])
    db_session.add(existing)
    db_session.commit()

    result = sync_lookup_column(
        db_session, "see", {"gaccha": ["gacchati"]}, use_raw_sql=use_raw_sql
    )
    row = _get(db_session, "gaccha")
    assert row is not None
    assert row.see_unpack == ["gacchati"]
    assert row.grammar_unpack == [["gacchati", "verb", "pr 3sg"]]
    assert (result.inserted, result.updated) == (0, 1)


def test_stale_key_with_other_value_is_cleared_not_deleted(
    db_session: Session, use_raw_sql: bool
) -> None:
    row = Lookup()
    row.lookup_key = "shared"
    row.see_pack(["x"])
    row.grammar_pack([["y", "verb", "g"]])
    db_session.add(row)
    db_session.commit()

    result = sync_lookup_column(db_session, "see", {}, use_raw_sql=use_raw_sql)
    refreshed = _get(db_session, "shared")
    assert refreshed is not None
    assert refreshed.see == ""
    assert refreshed.grammar_unpack == [["y", "verb", "g"]]
    assert (result.cleared, result.deleted) == (1, 0)


def test_stale_key_with_no_other_value_is_deleted(
    db_session: Session, use_raw_sql: bool
) -> None:
    row = Lookup()
    row.lookup_key = "orphan"
    row.see_pack(["gone"])
    db_session.add(row)
    db_session.commit()

    result = sync_lookup_column(db_session, "see", {}, use_raw_sql=use_raw_sql)
    assert _get(db_session, "orphan") is None
    assert (result.cleared, result.deleted) == (0, 1)


def test_clear_stale_false_leaves_stale_rows_untouched(
    db_session: Session, use_raw_sql: bool
) -> None:
    row = Lookup()
    row.lookup_key = "keep"
    row.see_pack(["z"])
    db_session.add(row)
    db_session.commit()

    result = sync_lookup_column(
        db_session, "see", {}, clear_stale=False, use_raw_sql=use_raw_sql
    )
    refreshed = _get(db_session, "keep")
    assert refreshed is not None
    assert refreshed.see_unpack == ["z"]
    assert (result.cleared, result.deleted) == (0, 0)


def test_pack_attr_override_for_variant(db_session: Session, use_raw_sql: bool) -> None:
    result = sync_lookup_column(
        db_session,
        "variant",
        {"v1": {"reading": "v2"}},
        pack_attr="variant_pack",
        use_raw_sql=use_raw_sql,
    )
    row = _get(db_session, "v1")
    assert row is not None
    assert row.variant_unpack == {"reading": "v2"}
    assert result.inserted == 1


def test_mixed_update_insert_clear_delete_in_one_call(
    db_session: Session, use_raw_sql: bool
) -> None:
    to_update = Lookup()
    to_update.lookup_key = "upd"
    to_update.see_pack(["before"])

    stale_clear = Lookup()
    stale_clear.lookup_key = "stale_clear"
    stale_clear.see_pack(["bye"])
    stale_clear.grammar_pack([["g", "verb", "g"]])

    stale_delete = Lookup()
    stale_delete.lookup_key = "stale_delete"
    stale_delete.see_pack(["bye"])

    db_session.add_all([to_update, stale_clear, stale_delete])
    db_session.commit()

    data = {"upd": ["after"], "new": ["fresh"]}
    result = sync_lookup_column(db_session, "see", data, use_raw_sql=use_raw_sql)

    assert _get(db_session, "upd").see_unpack == ["after"]  # type: ignore[union-attr]
    assert _get(db_session, "new").see_unpack == ["fresh"]  # type: ignore[union-attr]
    assert _get(db_session, "stale_clear").see == ""  # type: ignore[union-attr]
    assert _get(db_session, "stale_delete") is None
    assert (result.updated, result.inserted, result.cleared, result.deleted) == (
        1,
        1,
        1,
        1,
    )


def test_chunking_handles_more_keys_than_chunk_size(
    db_session: Session, use_raw_sql: bool
) -> None:
    data = {f"key{i}": [f"hw{i}"] for i in range(25)}
    result = sync_lookup_column(
        db_session, "see", data, chunk_size=10, use_raw_sql=use_raw_sql
    )
    assert result.inserted == 25
    assert db_session.query(Lookup).count() == 25
    assert _get(db_session, "key24").see_unpack == ["hw24"]  # type: ignore[union-attr]
