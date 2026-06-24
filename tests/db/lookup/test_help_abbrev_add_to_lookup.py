from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.lookup.help_abbrev_add_to_lookup import (
    add_abbreviations,
    add_abbreviations_other,
    add_help,
    normalize_other_abbreviation_key,
)
from db.models import Base, Lookup


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


class _MockPth:
    """Sentinel so attribute access on pth succeeds; value is ignored by monkeypatched readers."""

    def __getattr__(self, name: str) -> str:
        return name


@dataclass
class MockGlobalVars:
    db_session: Session
    pth: Any = None

    def __post_init__(self) -> None:
        if self.pth is None:
            self.pth = _MockPth()


def _get(session: Session, key: str) -> Lookup | None:
    return session.query(Lookup).filter(Lookup.lookup_key == key).first()


def test_add_help_inserts_new_key(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_as_dict",
        lambda _path: {"sutta": {"meaning": "a discourse"}},
    )
    g = MockGlobalVars(db_session=db_session)
    add_help(g)  # type: ignore[arg-type]
    row = _get(db_session, "sutta")
    assert row is not None
    assert row.help_unpack == "a discourse"


def test_add_help_updates_existing_key(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    existing = Lookup()
    existing.lookup_key = "sutta"
    existing.help_pack("old meaning")
    db_session.add(existing)
    db_session.commit()

    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_as_dict",
        lambda _path: {"sutta": {"meaning": "new meaning"}},
    )
    g = MockGlobalVars(db_session=db_session)
    add_help(g)  # type: ignore[arg-type]
    row = _get(db_session, "sutta")
    assert row is not None
    assert row.help_unpack == "new meaning"


def test_add_help_clears_stale(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = Lookup()
    row.lookup_key = "stale"
    row.help_pack("old help")
    row.grammar_pack([["karoti", "verb", "pr 3sg"]])
    db_session.add(row)
    db_session.commit()

    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_as_dict",
        lambda _path: {},
    )
    g = MockGlobalVars(db_session=db_session)
    add_help(g)  # type: ignore[arg-type]
    refreshed = _get(db_session, "stale")
    assert refreshed is not None
    assert refreshed.help == ""
    assert refreshed.grammar_unpack == [["karoti", "verb", "pr 3sg"]]


def test_add_help_deletes_stale_orphan(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    row = Lookup()
    row.lookup_key = "orphan"
    row.help_pack("only help")
    db_session.add(row)
    db_session.commit()

    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_as_dict",
        lambda _path: {},
    )
    g = MockGlobalVars(db_session=db_session)
    add_help(g)  # type: ignore[arg-type]
    assert _get(db_session, "orphan") is None


def test_add_abbreviations_inserts(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_as_dict",
        lambda _path: {"opt.": {"abbreviation": "opt.", "meaning": "optative"}},
    )
    g = MockGlobalVars(db_session=db_session)
    add_abbreviations(g)  # type: ignore[arg-type]
    row = _get(db_session, "opt.")
    assert row is not None
    assert row.abbrev_unpack == {"abbreviation": "opt.", "meaning": "optative"}


def test_add_abbreviations_other_groups_dotted_and_undotted(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "db.lookup.help_abbrev_add_to_lookup.read_tsv_dict",
        lambda _path: [
            {
                "abbreviation": "abbr.",
                "source": "PTS",
                "meaning": "abbreviation (dotted)",
                "notes": "",
            },
            {
                "abbreviation": "abbr",
                "source": "CPD",
                "meaning": "abbreviation (plain)",
                "notes": "",
            },
        ],
    )
    g = MockGlobalVars(db_session=db_session)
    add_abbreviations_other(g)  # type: ignore[arg-type]

    dotted_row = _get(db_session, "abbr.")
    assert dotted_row is None

    row = _get(db_session, "abbr")
    assert row is not None
    entries = row.abbrev_other_unpack
    assert len(entries) == 2
    sources = {e["source"] for e in entries}
    assert sources == {"PTS", "CPD"}


@pytest.mark.parametrize(
    "key, expected",
    [
        ("", ""),
        (".", ""),
        ("abl.", "abl"),
        ("AAWG", "AAWG"),
        ("a.b.", "a.b"),
        ("abc..", "abc."),
        ("Abh.", "Abh"),
        ("Artha-s.", "Artha-s"),
        ("-Up", "-Up"),
    ],
)
def test_normalize_strips_single_trailing_dot(key: str, expected: str) -> None:
    assert normalize_other_abbreviation_key(key) == expected
