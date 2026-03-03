# -*- coding: utf-8 -*-
"""Tests for Root CRUD methods in gui2.database_manager."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from db.models import Base, DpdHeadword, DpdRoot
from gui2.database_manager import DatabaseManager
from tools.pali_sort_key import pali_sort_key


@pytest.fixture
def db_session() -> Session:  # type: ignore
    """Create an in-memory SQLite session with all tables."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    root_a = DpdRoot(root="√kar", root_meaning="to do", root_group=1, root_sign="o")
    root_b = DpdRoot(root="√bhū", root_meaning="to be", root_group=1, root_sign="a")
    session.add_all([root_a, root_b])

    hw = DpdHeadword(
        id=1,
        lemma_1="karoti 1",
        pos="v",
        grammar="pr. 3sg.",
        meaning_1="does, makes",
        root_key="√kar",
    )
    session.add(hw)
    session.commit()
    yield session  # type: ignore
    session.close()


@pytest.fixture
def db_manager(db_session: Session) -> DatabaseManager:
    """DatabaseManager with its session replaced by the in-memory one."""
    manager = object.__new__(DatabaseManager)
    manager.db_session = db_session
    return manager


# ── Test: get_all_root_keys_sorted ──────────────────────────────────────────


def test_get_all_root_keys_sorted_returns_sorted_list(db_manager: DatabaseManager):
    keys = db_manager.get_all_root_keys_sorted()
    assert isinstance(keys, list)
    assert "√bhū" in keys
    assert "√kar" in keys
    assert keys == sorted(keys, key=pali_sort_key)


# ── Test: get_root_by_key ────────────────────────────────────────────────────


def test_get_root_by_key_returns_correct_root(db_manager: DatabaseManager):
    root = db_manager.get_root_by_key("√kar")
    assert root is not None
    assert root.root == "√kar"
    assert root.root_meaning == "to do"


def test_get_root_by_key_returns_none_for_missing(db_manager: DatabaseManager):
    root = db_manager.get_root_by_key("√nonexistent")
    assert root is None


# ── Test: add_root_to_db ─────────────────────────────────────────────────────


def test_add_root_to_db_inserts_new_root(
    db_manager: DatabaseManager, db_session: Session
):
    new_root = DpdRoot(root="√gam", root_meaning="to go", root_group=1, root_sign="a")
    success, msg = db_manager.add_root_to_db(new_root)
    assert success is True
    assert msg == ""

    fetched = db_session.query(DpdRoot).filter_by(root="√gam").first()
    assert fetched is not None
    assert fetched.root_meaning == "to go"


def test_add_root_to_db_fails_on_duplicate_key(db_manager: DatabaseManager):
    duplicate = DpdRoot(root="√kar", root_meaning="duplicate")
    success, msg = db_manager.add_root_to_db(duplicate)
    assert success is False
    assert msg != ""


# ── Test: update_root_in_db ──────────────────────────────────────────────────


def test_update_root_in_db_updates_fields(
    db_manager: DatabaseManager, db_session: Session
):
    root = db_session.query(DpdRoot).filter_by(root="√kar").first()
    assert root is not None
    root.root_meaning = "to perform"
    success, msg = db_manager.update_root_in_db("√kar", root)
    assert success is True

    fetched = db_session.query(DpdRoot).filter_by(root="√kar").first()
    assert fetched is not None
    assert fetched.root_meaning == "to perform"


def test_update_root_in_db_renames_primary_key(
    db_manager: DatabaseManager, db_session: Session
):
    new_root = DpdRoot(root="√kara", root_meaning="to do", root_group=1, root_sign="o")
    success, msg = db_manager.update_root_in_db("√kar", new_root)
    assert success is True

    old = db_session.query(DpdRoot).filter_by(root="√kar").first()
    new = db_session.query(DpdRoot).filter_by(root="√kara").first()
    assert old is None
    assert new is not None


def test_update_root_in_db_cascades_to_headwords(
    db_manager: DatabaseManager, db_session: Session
):
    new_root = DpdRoot(root="√kara", root_meaning="to do", root_group=1, root_sign="o")
    success, _ = db_manager.update_root_in_db("√kar", new_root)
    assert success is True

    hw = db_session.query(DpdHeadword).filter_by(id=1).first()
    assert hw is not None
    assert hw.root_key == "√kara"


# ── Test: delete_root_in_db ──────────────────────────────────────────────────


def test_delete_root_in_db_removes_root(
    db_manager: DatabaseManager, db_session: Session
):
    success, msg = db_manager.delete_root_in_db("√bhū")
    assert success is True

    fetched = db_session.query(DpdRoot).filter_by(root="√bhū").first()
    assert fetched is None


def test_delete_root_in_db_returns_false_for_missing(db_manager: DatabaseManager):
    success, msg = db_manager.delete_root_in_db("√nonexistent")
    assert success is False


# ── Test: get_root_headword_count ────────────────────────────────────────────


def test_get_root_headword_count_returns_correct_count(db_manager: DatabaseManager):
    count = db_manager.get_root_headword_count("√kar")
    assert count == 1


def test_get_root_headword_count_returns_zero_for_no_headwords(
    db_manager: DatabaseManager,
):
    count = db_manager.get_root_headword_count("√bhū")
    assert count == 0
