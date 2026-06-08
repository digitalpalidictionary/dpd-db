# -*- coding: utf-8 -*-
"""Tests for db/lookup/see.py.

Drives the real ``load_see_dict`` and ``add_see`` functions against an in-memory
SQLite db (real Lookup model, no mocks). Replaces the previous version, which
reimplemented the logic in raw sqlite3 and never called see.py at all.
"""

from collections import defaultdict
from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.lookup.see import GlobalVars, add_see, load_see_dict
from db.models import Base, Lookup


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def _make_g(session: Session, see_dict: dict[str, set[str]]) -> GlobalVars:
    g = object.__new__(GlobalVars)
    g.db_session = session
    g.see_dict = defaultdict(set, see_dict)
    return g


def _get(session: Session, key: str) -> Lookup | None:
    return session.query(Lookup).filter(Lookup.lookup_key == key).first()


def test_load_see_dict_reads_tsv(tmp_path) -> None:
    tsv = tmp_path / "see.tsv"
    tsv.write_text(
        "see\theadword\nkarohi\tkaroti\nkarohi\tkaroti 2\n", encoding="utf-8"
    )
    g = object.__new__(GlobalVars)
    g.pth = SimpleNamespace(see_path=tsv)  # type: ignore[assignment]

    load_see_dict(g)

    assert g.see_dict["karohi"] == {"karoti", "karoti 2"}


def test_add_see_inserts_new_entry(db_session: Session) -> None:
    g = _make_g(db_session, {"karohi": {"karoti"}})

    add_see(g)

    row = _get(db_session, "karohi")
    assert row is not None
    assert row.see_unpack == ["karoti"]


def test_add_see_updates_existing_entry(db_session: Session) -> None:
    existing = Lookup()
    existing.lookup_key = "karohi"
    existing.see_pack(["old_headword"])
    db_session.add(existing)
    db_session.commit()

    g = _make_g(db_session, {"karohi": {"karoti"}})
    add_see(g)

    row = _get(db_session, "karohi")
    assert row is not None
    assert row.see_unpack == ["karoti"]


def test_add_see_clears_stale_entry_with_other_value(db_session: Session) -> None:
    """The fix: a see entry no longer in the TSV is now cleared (was dead code)."""
    stale = Lookup()
    stale.lookup_key = "staleword"
    stale.see_pack(["someheadword"])
    stale.grammar_pack([["x", "verb", "g"]])
    db_session.add(stale)
    db_session.commit()

    g = _make_g(db_session, {"karohi": {"karoti"}})
    add_see(g)

    refreshed = _get(db_session, "staleword")
    assert refreshed is not None
    assert refreshed.see == ""
    assert refreshed.grammar_unpack == [["x", "verb", "g"]]


def test_add_see_deletes_stale_entry_with_no_other_value(db_session: Session) -> None:
    stale = Lookup()
    stale.lookup_key = "staleword"
    stale.see_pack(["someheadword"])
    db_session.add(stale)
    db_session.commit()

    g = _make_g(db_session, {"karohi": {"karoti"}})
    add_see(g)

    assert _get(db_session, "staleword") is None
    assert _get(db_session, "karohi") is not None
