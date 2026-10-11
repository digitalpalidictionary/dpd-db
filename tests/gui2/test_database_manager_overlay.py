# -*- coding: utf-8 -*-
"""A contributor's own JSON edits shown on top of the db (set_overlay)."""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, DpdHeadword
from gui2.database_manager import DatabaseManager


@pytest.fixture
def session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)()
    db_session.add_all(
        [
            DpdHeadword(id=1, lemma_1="assa 1", meaning_1="horse"),
            DpdHeadword(id=2, lemma_1="buddha 1", meaning_1="awakened"),
        ]
    )
    db_session.commit()
    yield db_session
    db_session.close()


@pytest.fixture
def manager(session: Session) -> DatabaseManager:
    manager = object.__new__(DatabaseManager)
    manager.db_session = session
    manager._own_edits = None
    return manager


def test_no_overlay_returns_db_rows(manager: DatabaseManager) -> None:
    word = manager.get_headword_by_id(1)
    assert word is not None
    assert word.meaning_1 == "horse"
    assert manager.get_next_id() == 3


def test_own_correction_beats_db_row(manager: DatabaseManager) -> None:
    corrections = {"alice_1": {"id": 1, "lemma_1": "assa 1", "meaning_1": "mine"}}
    manager.set_overlay(lambda: (corrections, {}))

    by_id = manager.get_headword_by_id(1)
    by_lemma = manager.get_headword_by_lemma("assa 1")
    assert by_id is not None and by_lemma is not None
    assert by_id.meaning_1 == "mine"
    assert by_lemma.meaning_1 == "mine"


def test_word_without_own_edit_comes_from_db(manager: DatabaseManager) -> None:
    corrections = {"alice_1": {"id": 1, "lemma_1": "assa 1", "meaning_1": "mine"}}
    manager.set_overlay(lambda: (corrections, {}))

    word = manager.get_headword_by_id(2)
    assert word is not None
    assert word.meaning_1 == "awakened"


def test_own_addition_found_by_id_and_lemma(manager: DatabaseManager) -> None:
    additions = {"alice_9": {"id": 9, "lemma_1": "new 1", "meaning_1": "fresh"}}
    manager.set_overlay(lambda: ({}, additions))

    by_id = manager.get_headword_by_id(9)
    by_lemma = manager.get_headword_by_lemma("new 1")
    assert by_id is not None and by_lemma is not None
    assert by_id.lemma_1 == "new 1"
    assert by_lemma.id == 9


def test_correction_wins_over_addition_for_same_id(manager: DatabaseManager) -> None:
    corrections = {"alice_1": {"id": 1, "meaning_1": "correction"}}
    additions = {"alice_1": {"id": 1, "meaning_1": "addition"}}
    manager.set_overlay(lambda: (corrections, additions))

    word = manager.get_headword_by_id(1)
    assert word is not None
    assert word.meaning_1 == "correction"


def test_next_id_skips_own_additions(manager: DatabaseManager) -> None:
    additions = {"alice_9": {"id": 9}, "alice_4": {"id": 4}}
    manager.set_overlay(lambda: ({}, additions))
    assert manager.get_next_id() == 10


def test_overlay_reads_live_dicts(manager: DatabaseManager) -> None:
    additions: dict[str, dict] = {}
    manager.set_overlay(lambda: ({}, additions))
    assert manager.get_headword_by_id(9) is None

    additions["alice_9"] = {"id": 9, "lemma_1": "new 1"}
    assert manager.get_headword_by_id(9) is not None


def test_all_lemma_1_includes_own_additions(manager: DatabaseManager) -> None:
    additions = {"alice_9": {"id": 9, "lemma_1": "new 1"}}
    manager.set_overlay(lambda: ({}, additions))

    manager.get_all_lemma_1_and_lemma_clean()
    assert manager.all_lemma_1 == {"assa 1", "buddha 1", "new 1"}


def test_overlay_word_is_not_in_a_session(manager: DatabaseManager) -> None:
    corrections = {"alice_1": {"id": 1, "lemma_1": "assa 1", "meaning_1": "mine"}}
    manager.set_overlay(lambda: (corrections, {}))

    word = manager.get_headword_by_id(1)
    assert word is not None
    assert inspect(word).session is None
