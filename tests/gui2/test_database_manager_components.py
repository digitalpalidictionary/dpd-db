# -*- coding: utf-8 -*-
"""Tests for the compound components map used by the pass2 preprocessor's
"in comps" mode in gui2.database_manager."""

import threading
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from db.models import Base, DpdHeadword
from gui2.database_manager import DatabaseManager


@pytest.fixture
def engine_and_session() -> Generator[tuple[Engine, Session], None, None]:
    """In-memory SQLite engine + session with compound and simple headwords."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    session.add_all(
        [
            # a compound: two components, two inflections
            DpdHeadword(
                id=1,
                lemma_1="assakhaluṅka 1",
                pos="masc",
                grammar="masc, comp",
                construction="assa + khaluṅka",
                inflections="assakhaluṅka,assakhaluṅkā",
            ),
            # a compound with a suffix component ("ka" is a suffix below)
            DpdHeadword(
                id=2,
                lemma_1="dhammika 1",
                pos="adj",
                grammar="adj, comp",
                construction="dhamma + ika",
                inflections="dhammika",
            ),
            # not a compound (no "comp" in grammar)
            DpdHeadword(
                id=3,
                lemma_1="assa 1",
                pos="masc",
                grammar="masc",
                construction="assa",
                inflections="assa,assā",
            ),
            # comp in grammar but single-part construction — excluded
            DpdHeadword(
                id=4,
                lemma_1="khaluṅka 1",
                pos="masc",
                grammar="masc, comp",
                construction="khaluṅka",
                inflections="khaluṅka",
            ),
            # supplies the "ika" suffix via make_pass2_lists
            DpdHeadword(
                id=5,
                lemma_1="ika 1",
                pos="suffix",
                grammar="suffix",
                suffix="ika",
                inflections="ika",
            ),
        ]
    )
    session.commit()
    yield engine, session
    session.close()


@pytest.fixture
def db_manager(engine_and_session: tuple[Engine, Session]) -> DatabaseManager:
    """DatabaseManager with only the corpus-cache state initialized."""
    _, session = engine_and_session
    manager = object.__new__(DatabaseManager)
    manager.db_session = session
    manager._corpus_stale = True
    manager._corpus_gen = 0
    manager._corpus_lock = threading.Lock()
    manager._inflections_gen = -1
    manager._pass2_gen = -1
    manager._components_gen = -1
    manager.compound_components_map = {}
    return manager


def test_compound_inflections_map_to_components(db_manager: DatabaseManager):
    db_manager.make_compound_components_map()
    assert db_manager.compound_components_map["assakhaluṅka"] == [
        "assa",
        "khaluṅka",
    ]
    assert db_manager.compound_components_map["assakhaluṅkā"] == [
        "assa",
        "khaluṅka",
    ]


def test_empty_string_never_a_map_key(db_manager: DatabaseManager):
    # inflections_list_all yields "" for empty inflections columns
    # (all fixture rows have empty inflections_api_ca_eva_iti)
    db_manager.make_compound_components_map()
    assert "" not in db_manager.compound_components_map


def test_non_compound_and_single_part_excluded(db_manager: DatabaseManager):
    db_manager.make_compound_components_map()
    # "assa" is not a compound; "khaluṅka" has a single-part construction
    assert "assa" not in db_manager.compound_components_map
    assert "khaluṅka" not in db_manager.compound_components_map


def test_suffixes_stripped_from_components(db_manager: DatabaseManager):
    db_manager.make_compound_components_map()
    assert db_manager.compound_components_map["dhammika"] == ["dhamma"]


def test_map_cached_for_same_corpus_gen(db_manager: DatabaseManager):
    db_manager.make_compound_components_map()
    first = db_manager.compound_components_map
    db_manager.make_compound_components_map()
    assert db_manager.compound_components_map is first


def test_map_rebuilds_after_corpus_stale(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    _, session = engine_and_session
    db_manager.make_compound_components_map()
    first = db_manager.compound_components_map

    session.add(
        DpdHeadword(
            id=6,
            lemma_1="dhammacakka 1",
            pos="nt",
            grammar="nt, comp",
            construction="dhamma + cakka",
            inflections="dhammacakka",
        )
    )
    session.commit()
    db_manager.mark_corpus_stale()

    db_manager.make_compound_components_map()
    assert db_manager.compound_components_map is not first
    assert db_manager.compound_components_map["dhammacakka"] == ["dhamma", "cakka"]
