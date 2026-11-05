# -*- coding: utf-8 -*-
"""Tests for the cached corpus load and the coalescing detector rebuild
worker in gui2.database_manager."""

import threading
import time
from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, event, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import gui2.database_manager as database_manager_module
from db.models import Base, DpdHeadword, Lookup
from gui2.database_manager import DatabaseManager
from tools.hashed_words import HashedWords
from tools.synonym_variant import RelationshipDetector


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
    """initialize_db() must flip db_loaded True once the lookup sets and the
    decon cache are ready — no corpus load or detector build happens there
    any more. Stub the file-backed get_all_* helpers."""
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

    assert db_manager.is_db_loaded() is False
    db_manager.initialize_db()
    assert db_manager.is_db_loaded() is True


def test_initialize_db_does_not_build_detector(
    db_manager: DatabaseManager, monkeypatch: pytest.MonkeyPatch
):
    """initialize_db() must leave the detector unbuilt — it is lazy now, and
    the corpus load it would trigger must stay off the db-loaded path."""
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

    db_manager.initialize_db()
    assert getattr(db_manager, "_relationship_detector", None) is None
    assert getattr(db_manager, "db", None) is None


# ── derived sets ─────────────────────────────────────────────────────────────


def test_make_inflections_lists_derives_from_corpus(db_manager: DatabaseManager):
    db_manager.make_inflections_lists()
    all_inflections = db_manager.all_inflections
    missing_meaning = db_manager.all_inflections_missing_meaning
    assert isinstance(all_inflections, set)
    assert isinstance(missing_meaning, set)
    assert {"kata", "katā", "gata", "gatā", "dhamma", "dhammā"} <= all_inflections
    # only the meaning-less headword contributes to missing_meaning
    assert {"kata", "katā"} <= missing_meaning
    assert "gata" not in missing_meaning


def test_make_pass2_lists_derives_from_corpus(db_manager: DatabaseManager):
    db_manager.make_pass2_lists()
    # gata: meaning_1 but no source_1 → missing example
    assert {"gata", "gatā"} <= db_manager.all_inflections_missing_example
    # dhamma: early sutta source → not missing
    assert "dhamma" not in db_manager.all_inflections_missing_example
    assert db_manager.all_suffixes == {"ta", "a"}
    # the commentary-book rule agrees on all three
    assert {"kata", "gata"} <= db_manager.all_inflections_missing_any_example
    assert "dhamma" not in db_manager.all_inflections_missing_any_example


def test_commentary_book_counts_late_example_as_done(
    db_manager: DatabaseManager, engine_and_session: tuple[Engine, Session]
):
    _, session = engine_and_session
    session.add(
        DpdHeadword(
            id=4,
            lemma_1="vutta 1",
            pos="pp",
            meaning_1="said",
            source_1="DNa1",
            example_1="vuttaṁ hetaṁ",
            inflections="vutta",
        )
    )
    lookup = Lookup(lookup_key="vutta")
    lookup.headwords_pack([4])
    session.add(lookup)
    session.commit()
    db_manager.mark_corpus_stale()

    db_manager.make_pass2_lists()
    assert "vutta" in db_manager.all_inflections_missing_example
    assert "vutta" not in db_manager.all_inflections_missing_any_example
    assert [h.id for h in db_manager.get_headwords("vutta")] == [4]
    assert db_manager.get_headwords("vutta", commentary_book=True) == []


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


def test_rename_pattern_in_headwords_marks_corpus_stale(db_manager: DatabaseManager):
    db_manager.db_session.query(DpdHeadword).filter_by(id=2).update({"pattern": "old"})
    db_manager.db_session.commit()
    db_manager.load_corpus()
    assert db_manager._corpus_stale is False

    count = db_manager.rename_pattern_in_headwords("old", "new")

    assert count == 1
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


# ── contributor role: slim corpus and compact inflection sets ───────────────


@pytest.fixture
def contributor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the DatabaseManager behave as a contributor-server instance."""
    monkeypatch.setattr(database_manager_module, "is_headless_server", lambda: True)


def unloaded(row: DpdHeadword) -> set[str]:
    """Columns not loaded on the row (relationships are always unloaded)."""
    columns = {column.name for column in DpdHeadword.__table__.columns}
    return set(inspect(row).unloaded) & columns


def test_desktop_corpus_defers_only_the_five_big_columns(db_manager: DatabaseManager):
    row = db_manager.load_corpus()[0]
    assert unloaded(row) == {
        "inflections_html",
        "freq_html",
        "inflections_sinhala",
        "inflections_devanagari",
        "inflections_thai",
    }


def test_contributor_corpus_loads_only_the_detector_columns(
    db_manager: DatabaseManager, contributor: None
):
    corpus = db_manager.load_corpus()
    for row in corpus:
        assert {
            "example_1",
            "commentary",
            "inflections",
            "inflections_api_ca_eva_iti",
        } <= (unloaded(row))
        assert not {"lemma_1", "meaning_1", "pos", "grammar", "construction"} & (
            unloaded(row)
        )


def test_contributor_corpus_loads_freq_data_only_without_a_meaning(
    db_manager: DatabaseManager, contributor: None
):
    by_lemma = {row.lemma_1: row for row in db_manager.load_corpus()}
    assert "freq_data" not in unloaded(by_lemma["kata 1"])  # meaning_1 is empty
    assert "freq_data" in unloaded(by_lemma["gata 1"])  # has a meaning


def test_contributor_corpus_keeps_every_row_in_id_order(
    db_manager: DatabaseManager, contributor: None
):
    assert [row.id for row in db_manager.load_corpus()] == [1, 2, 3]


def test_contributor_detector_answers_like_the_full_corpus(
    db_manager: DatabaseManager,
    engine_and_session: tuple[Engine, Session],
    contributor: None,
    monkeypatch: pytest.MonkeyPatch,
):
    _, session = engine_and_session

    def answers(rows: list[DpdHeadword]) -> dict[int, tuple[list[str], list]]:
        detector = RelationshipDetector(rows)
        return {
            row.id: (detector.find_synonyms(row), detector.find_phonetic_variants(row))
            for row in rows
        }

    slim_rows = db_manager.load_corpus()
    # detached rows raise on any column the slim load left out
    session.expunge_all()
    slim = answers(slim_rows)

    monkeypatch.setattr(database_manager_module, "is_headless_server", lambda: False)
    db_manager.mark_corpus_stale()
    assert answers(db_manager.load_corpus()) == slim


def test_contributor_inflection_sets_are_compact_and_leave_the_corpus_alone(
    db_manager: DatabaseManager, contributor: None
):
    db_manager.make_inflections_lists()
    assert isinstance(db_manager.all_inflections, HashedWords)
    assert isinstance(db_manager.all_inflections_missing_meaning, HashedWords)
    assert getattr(db_manager, "db", None) is None


def test_contributor_inflection_sets_answer_like_the_desktop_sets(
    db_manager: DatabaseManager, monkeypatch: pytest.MonkeyPatch
):
    db_manager.make_inflections_lists()
    assert isinstance(db_manager.all_inflections, set)
    assert isinstance(db_manager.all_inflections_missing_meaning, set)
    desktop_all = set(db_manager.all_inflections)
    desktop_missing = set(db_manager.all_inflections_missing_meaning)

    monkeypatch.setattr(database_manager_module, "is_headless_server", lambda: True)
    db_manager.mark_corpus_stale()
    db_manager.make_inflections_lists()
    for word in desktop_all | {"zzz", "katax", "gat"}:
        assert (word in db_manager.all_inflections) == (word in desktop_all)
    for word in desktop_missing | {"gata", "dhamma", "zzz"}:
        assert (word in db_manager.all_inflections_missing_meaning) == (
            word in desktop_missing
        )


def test_contributor_inflection_sets_rebuild_only_after_stale(
    db_manager: DatabaseManager,
    engine_and_session: tuple[Engine, Session],
    contributor: None,
):
    _, session = engine_and_session
    db_manager.make_inflections_lists()
    session.add(DpdHeadword(id=4, lemma_1="magga 1", pos="masc", inflections="magga"))
    session.commit()

    db_manager.make_inflections_lists()
    assert "magga" not in db_manager.all_inflections

    db_manager.mark_corpus_stale()
    db_manager.make_inflections_lists()
    assert "magga" in db_manager.all_inflections


def test_contributor_inflection_sets_wait_for_the_corpus_lock(
    db_manager: DatabaseManager, contributor: None
):
    finished = threading.Event()

    def build() -> None:
        db_manager.make_inflections_lists()
        finished.set()

    builder = threading.Thread(target=build)
    with db_manager._corpus_lock:
        builder.start()
        assert not finished.wait(0.3)
    assert finished.wait(5)
    builder.join()


def test_contributor_inflection_sets_notice_a_stale_mark_during_the_build(
    db_manager: DatabaseManager,
    engine_and_session: tuple[Engine, Session],
    contributor: None,
    monkeypatch: pytest.MonkeyPatch,
):
    _, session = engine_and_session
    real_hashed_words = database_manager_module.HashedWords
    marked: list[bool] = []

    def hashed_words_with_a_refresh(words):
        if not marked:
            marked.append(True)
            db_manager.mark_corpus_stale()
        return real_hashed_words(words)

    monkeypatch.setattr(
        database_manager_module, "HashedWords", hashed_words_with_a_refresh
    )
    db_manager.make_inflections_lists()
    session.add(DpdHeadword(id=4, lemma_1="magga 1", pos="masc", inflections="magga"))
    session.commit()

    db_manager.make_inflections_lists()
    assert "magga" in db_manager.all_inflections


def test_contributor_inflection_sets_include_the_api_ca_eva_iti_column(
    db_manager: DatabaseManager,
    engine_and_session: tuple[Engine, Session],
    contributor: None,
):
    _, session = engine_and_session
    session.add(
        DpdHeadword(
            id=4,
            lemma_1="eva 1",
            pos="ind",
            meaning_1="",
            inflections="eva",
            inflections_api_ca_eva_iti="evaca",
        )
    )
    session.commit()
    db_manager.make_inflections_lists()
    assert "evaca" in db_manager.all_inflections
    assert "evaca" in db_manager.all_inflections_missing_meaning
