# -*- coding: utf-8 -*-
"""Tests for the cached corpus load and the coalescing detector rebuild
worker in gui2.database_manager."""

import threading
import time
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import gui2.database_manager as database_manager_module
from db.models import Base, DpdHeadword
from gui2.database_manager import DatabaseManager


@pytest.fixture
def engine_and_session() -> Generator[tuple[Engine, Session], None, None]:
    """In-memory SQLite engine + session with a small headword corpus."""
    # StaticPool + check_same_thread=False so the background rebuild
    # worker thread sees the same in-memory database.
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
            DpdHeadword(
                id=1,
                lemma_1="kata 1",
                pos="pp",
                meaning_1="",
                inflections="kata,katā",
            ),
            DpdHeadword(
                id=2,
                lemma_1="gata 1",
                pos="pp",
                meaning_1="gone",
                source_1="",
                suffix="ta",
                inflections="gata,gatā",
            ),
            DpdHeadword(
                id=3,
                lemma_1="dhamma 1",
                pos="masc",
                meaning_1="teaching",
                source_1="MN 1",
                example_1="dhammaṁ deseti",
                suffix="a",
                inflections="dhamma,dhammā",
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
    manager.db_loaded = False
    return manager


def count_headword_selects(engine: Engine) -> dict[str, int]:
    """Attach a counter for SELECTs on dpd_headwords."""
    counts = {"n": 0}

    @event.listens_for(engine, "before_cursor_execute")
    def _count(conn, cursor, statement, parameters, context, executemany) -> None:
        if statement.lstrip().upper().startswith("SELECT") and (
            "dpd_headwords" in statement
        ):
            counts["n"] += 1

    return counts


# ── load_corpus ──────────────────────────────────────────────────────────────


def test_load_corpus_loads_all_rows(db_manager: DatabaseManager):
    corpus = db_manager.load_corpus()
    assert len(corpus) == 3
    assert {hw.lemma_1 for hw in corpus} == {"kata 1", "gata 1", "dhamma 1"}


def test_load_corpus_is_cached(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    engine, _ = engine_and_session
    first = db_manager.load_corpus()
    counts = count_headword_selects(engine)
    second = db_manager.load_corpus()
    assert second is first
    assert counts["n"] == 0


def test_mark_corpus_stale_forces_reload(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    _, session = engine_and_session
    first = db_manager.load_corpus()

    session.add(DpdHeadword(id=4, lemma_1="magga 1", pos="masc", inflections="magga"))
    session.commit()

    # without staleness, the new row is not visible
    assert len(db_manager.load_corpus()) == 3

    db_manager.mark_corpus_stale()
    reloaded = db_manager.load_corpus()
    assert reloaded is not first
    assert len(reloaded) == 4


# ── db-loaded readiness gate ─────────────────────────────────────────────────


def test_is_db_loaded_false_before_init(db_manager: DatabaseManager):
    assert db_manager.is_db_loaded() is False


def test_is_db_loaded_true_after_flag_set(db_manager: DatabaseManager):
    db_manager.db_loaded = True
    assert db_manager.is_db_loaded() is True


def test_initialize_db_sets_db_loaded(
    db_manager: DatabaseManager, monkeypatch: pytest.MonkeyPatch
):
    """initialize_db() must flip db_loaded True after the corpus load so save
    paths stop being gated. Stub the file-backed get_all_* helpers; the corpus
    load runs against the in-memory fixture."""
    for name in (
        "get_all_lemma_1_and_lemma_clean",
        "get_all_pos",
        "get_all_roots",
        "get_all_root_families",
        "get_all_compound_families",
        "get_all_word_families",
        "get_all_patterns",
        "get_all_decon_no_headwords",
    ):
        monkeypatch.setattr(db_manager, name, lambda: None)
    monkeypatch.setattr(
        database_manager_module, "RelationshipDetector", lambda corpus: object()
    )

    assert db_manager.is_db_loaded() is False
    db_manager.initialize_db()
    assert db_manager.is_db_loaded() is True


# ── derived sets ─────────────────────────────────────────────────────────────


def test_make_inflections_lists_derives_from_corpus(db_manager: DatabaseManager):
    db_manager.make_inflections_lists()
    assert {"kata", "katā", "gata", "gatā", "dhamma", "dhammā"} <= (
        db_manager.all_inflections
    )
    # only the meaning-less headword contributes to missing_meaning
    assert {"kata", "katā"} <= db_manager.all_inflections_missing_meaning
    assert "gata" not in db_manager.all_inflections_missing_meaning


def test_make_pass2_lists_derives_from_corpus(db_manager: DatabaseManager):
    db_manager.make_pass2_lists()
    # gata: meaning_1 but no source_1 → missing example
    assert {"gata", "gatā"} <= db_manager.all_inflections_missing_example
    # dhamma: early sutta source → not missing
    assert "dhamma" not in db_manager.all_inflections_missing_example
    assert db_manager.all_suffixes == {"ta", "a"}


def test_derived_sets_share_one_corpus_load(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    engine, _ = engine_and_session
    db_manager.load_corpus()
    counts = count_headword_selects(engine)
    db_manager.make_inflections_lists()
    db_manager.make_pass2_lists()
    assert counts["n"] == 0


def test_make_inflections_lists_skips_rebuild_when_fresh(
    db_manager: DatabaseManager,
):
    db_manager.make_inflections_lists()
    first_set = db_manager.all_inflections
    db_manager.make_inflections_lists()
    assert db_manager.all_inflections is first_set


def test_make_inflections_lists_rebuilds_after_stale(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    _, session = engine_and_session
    db_manager.make_inflections_lists()
    first_set = db_manager.all_inflections

    session.add(
        DpdHeadword(id=4, lemma_1="magga 1", pos="masc", inflections="magga,maggā")
    )
    session.commit()
    db_manager.mark_corpus_stale()

    db_manager.make_inflections_lists()
    assert db_manager.all_inflections is not first_set
    assert "magga" in db_manager.all_inflections


# ── write paths mark the corpus stale ────────────────────────────────────────


def test_add_word_to_db_marks_corpus_stale(db_manager: DatabaseManager):
    db_manager.invalidate_relationship_detector = lambda: None  # type: ignore[method-assign]
    db_manager.load_corpus()
    assert db_manager._corpus_stale is False

    new_word = DpdHeadword(id=5, lemma_1="citta 1", pos="nt", inflections="citta")
    ok, _ = db_manager.add_word_to_db(new_word)
    assert ok
    assert db_manager._corpus_stale is True
    assert len(db_manager.load_corpus()) == 4


def test_update_word_in_db_marks_corpus_stale(db_manager: DatabaseManager):
    db_manager.invalidate_relationship_detector = lambda: None  # type: ignore[method-assign]
    db_manager.load_corpus()
    assert db_manager._corpus_stale is False

    word = DpdHeadword(id=2, lemma_1="gata 1", pos="pp", meaning_1="gone, went")
    ok, _ = db_manager.update_word_in_db(word)
    assert ok
    assert db_manager._corpus_stale is True


# ── detector rebuild worker (single, coalescing) ─────────────────────────────


class _CountingDetector:
    build_count = 0

    def __init__(self, headwords: list[DpdHeadword]) -> None:
        _CountingDetector.build_count += 1
        self.headwords = headwords


@pytest.fixture
def rebuild_manager(
    db_manager: DatabaseManager,
    engine_and_session: tuple[Engine, Session],
    monkeypatch: pytest.MonkeyPatch,
) -> DatabaseManager:
    """db_manager wired for real background detector rebuilds."""
    engine, _ = engine_and_session
    _CountingDetector.build_count = 0
    monkeypatch.setattr(database_manager_module, "DETECTOR_REBUILD_DEBOUNCE_SECS", 0.05)
    monkeypatch.setattr(
        database_manager_module, "RelationshipDetector", _CountingDetector
    )
    monkeypatch.setattr(
        database_manager_module, "get_db_session", lambda _: Session(bind=engine)
    )
    db_manager.pth = type("Pth", (), {"dpd_db_path": "unused"})()  # type: ignore[assignment]
    db_manager._relationship_detector = None
    db_manager._detector_rebuild_lock = threading.Lock()
    db_manager._detector_rebuild_pending = False
    db_manager._detector_rebuild_running = False
    return db_manager


def wait_until_idle(manager: DatabaseManager, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with manager._detector_rebuild_lock:
            if not manager._detector_rebuild_running:
                return
        time.sleep(0.01)
    raise AssertionError("detector rebuild worker never went idle")


def test_rapid_invalidations_coalesce_into_one_rebuild(
    rebuild_manager: DatabaseManager,
):
    for _ in range(5):
        rebuild_manager.invalidate_relationship_detector()
    wait_until_idle(rebuild_manager)
    assert _CountingDetector.build_count == 1
    assert isinstance(rebuild_manager._relationship_detector, _CountingDetector)


def test_invalidation_after_idle_rebuilds_again(rebuild_manager: DatabaseManager):
    rebuild_manager.invalidate_relationship_detector()
    wait_until_idle(rebuild_manager)
    assert _CountingDetector.build_count == 1

    rebuild_manager.invalidate_relationship_detector()
    wait_until_idle(rebuild_manager)
    assert _CountingDetector.build_count == 2
