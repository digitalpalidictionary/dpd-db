# -*- coding: utf-8 -*-
"""Tests for the inflection template methods in gui2.database_manager."""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.inflections.inflection_template_files import (
    TemplateFile,
    write_template,
)
from db.models import Base, DbInfo, DpdHeadword, InflectionTemplates
from gui2.database_manager import DatabaseManager
from tools.paths import ProjectPaths


@pytest.fixture
def tmp_pth(tmp_path) -> ProjectPaths:
    """ProjectPaths pointing into the temp dir."""
    return ProjectPaths(base_dir=tmp_path, create_dirs=False)


@pytest.fixture
def db_session(tmp_pth) -> Iterator[Session]:
    """In-memory SQLite session with all tables and two words."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    session.add_all(
        [
            DpdHeadword(
                id=1,
                lemma_1="avocado",
                pos="masc",
                stem="avocad",
                pattern="test pr",
                meaning_1="a fruit",
            ),
            DpdHeadword(
                id=2,
                lemma_1="banana",
                pos="masc",
                stem="banan",
                pattern="other pr",
                meaning_1="another fruit",
            ),
        ]
    )
    session.commit()
    yield session
    session.close()


@pytest.fixture
def db_manager(db_session: Session, tmp_pth: ProjectPaths) -> DatabaseManager:
    """DatabaseManager with its session and paths replaced by temp ones."""
    manager = object.__new__(DatabaseManager)
    manager.db_session = db_session
    manager.pth = tmp_pth
    return manager


@pytest.fixture
def template_files(tmp_pth: ProjectPaths) -> ProjectPaths:
    """One template written to the temp TSV files."""
    t = TemplateFile(
        pattern="test pr",
        like="ka",
        data=[
            [[""], ["sg"], [""], ["pl"]],
            [["nom"], ["o"], ["nom sg"], ["ā"]],
        ],
    )
    write_template(
        t, tmp_pth.inflection_templates_index_path, tmp_pth.inflection_templates_dir
    )
    return tmp_pth


def test_get_pattern_headword_count(db_manager: DatabaseManager):
    assert db_manager.get_pattern_headword_count("test pr") == 1
    assert db_manager.get_pattern_headword_count("other pr") == 1
    assert db_manager.get_pattern_headword_count("no pr") == 0


def test_rename_pattern_in_headwords(db_manager: DatabaseManager, db_session: Session):
    count = db_manager.rename_pattern_in_headwords("test pr", "renamed pr")
    assert count == 1
    hw = db_session.query(DpdHeadword).filter_by(id=1).one()
    assert hw.pattern == "renamed pr"


def test_rename_pattern_in_headwords_no_match(db_manager: DatabaseManager):
    count = db_manager.rename_pattern_in_headwords("missing pr", "x pr")
    assert count == 0


def test_sync_inflection_templates(
    db_manager: DatabaseManager, db_session: Session, template_files
):
    """Sync adds the template, lists it as pending, refreshes patterns."""
    changed = db_manager.sync_inflection_templates()
    assert changed == ["test pr"]

    row = db_session.query(InflectionTemplates).filter_by(pattern="test pr").one()
    assert row.like == "ka"

    pending = db_session.query(DbInfo).filter_by(key="changed_templates_list").one()
    assert pending.value_unpack == ["test pr"]

    assert db_manager.all_patterns == {"test pr"}


def test_sync_inflection_templates_no_change(
    db_manager: DatabaseManager, template_files
):
    """A second sync of the same files changes nothing."""
    db_manager.sync_inflection_templates()
    changed = db_manager.sync_inflection_templates()
    assert changed == []
