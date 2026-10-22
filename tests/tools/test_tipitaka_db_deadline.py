import threading
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import tools.tipitaka_db as tipitaka_db
from tools.search_deadline import (
    SearchStopped,
    SearchTimeout,
    install_regexp,
    regex_deadline,
)

SLOW_PATTERN = r"^(a|a)+$"


@pytest.fixture
def tt_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'tt.db'}")
    with engine.begin() as conn:
        conn.execute(text("create table t1 (pali_text text, english_translation text)"))
        conn.execute(text("insert into t1 values (:p, 'eng')"), {"p": "a" * 60 + "b"})

    def make_session() -> Session:
        session = sessionmaker(bind=engine)()
        install_regexp(session)
        return session

    monkeypatch.setattr(tipitaka_db, "get_tipitaka_db_session", make_session)


def test_fast_pattern_still_returns_rows(tt_session: None) -> None:
    results = tipitaka_db.search_tables_union(["t1"], {"t1": "book"}, "a+b")
    assert len(results) == 1


def test_timeout_is_raised_not_swallowed(tt_session: None) -> None:
    with regex_deadline(0.3):
        with pytest.raises(SearchTimeout):
            tipitaka_db.search_tables_union(["t1"], {"t1": "book"}, SLOW_PATTERN)


@pytest.fixture
def many_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'many.db'}")
    with engine.begin() as conn:
        for table in ("t1", "t2"):
            conn.execute(
                text(f"create table {table} (pali_text text, english_translation text)")
            )
            conn.execute(
                text(f"insert into {table} values (:p, 'eng')"),
                [{"p": f"dhamma {i}"} for i in range(300)],
            )

    def make_session() -> Session:
        session = sessionmaker(bind=engine)()
        install_regexp(session)
        return session

    monkeypatch.setattr(tipitaka_db, "get_tipitaka_db_session", make_session)


def test_limit_stops_loading_rows(many_rows: None) -> None:
    book_lookup = {"t1": "book", "t2": "book"}
    unlimited = tipitaka_db.search_tables_union(["t1", "t2"], book_lookup, "dhamma")
    limited = tipitaka_db.search_tables_union(
        ["t1", "t2"], book_lookup, "dhamma", limit=101
    )
    assert len(unlimited) == 600
    assert len(limited) == 101


@pytest.mark.parametrize("pattern", ["(", "(?:a{1500}){1500}"])
def test_rejected_pattern_is_raised_not_swallowed(
    tt_session: None, pattern: str
) -> None:
    with regex_deadline(5):
        with pytest.raises(SearchStopped):
            tipitaka_db.search_tables_union(["t1"], {"t1": "book"}, pattern)


def test_single_table_search_honours_the_limit() -> None:
    from tools.paths import ProjectPaths

    if not ProjectPaths().tipitaka_translation_db_path.exists():
        pytest.skip("translation database not present")
    table = tipitaka_db.get_table_names_for_book("dn1")[0]
    unlimited = tipitaka_db.search_tipitaka(table, ".")
    limited = tipitaka_db.search_tipitaka(table, ".", limit=5)
    assert len(unlimited) > 5
    assert len(limited) == 5


@pytest.mark.parametrize("pattern", ["(?:a+)b", "a:b|a+b", "it's|a+b"])
def test_pattern_with_a_colon_or_quote_uses_the_combined_query(
    tt_session: None, pattern: str
) -> None:
    """The per-table fallback cannot read this fixture's tables, so a row only
    comes back if the combined query itself ran."""
    results = tipitaka_db.search_tables_union(["t1"], {"t1": "book"}, pattern)
    assert len(results) == 1


@pytest.fixture
def big_table(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'big.db'}")
    with engine.begin() as conn:
        conn.execute(text("create table t1 (pali_text text, english_translation text)"))
        conn.execute(
            text("insert into t1 values (:p, 'eng')"),
            [{"p": f"evaṃ me sutaṃ ekaṃ samayaṃ {i}"} for i in range(150_000)],
        )

    def make_session() -> Session:
        session = sessionmaker(bind=engine)()
        install_regexp(session)
        return session

    monkeypatch.setattr(tipitaka_db, "get_tipitaka_db_session", make_session)


def test_four_ordinary_searches_at_once_do_not_time_each_other_out(
    big_table: None,
) -> None:
    """A full scan that matches nothing, four at once. Each needs ~0.3 s of its
    own CPU but ~1.2 s of wall time while the four share the global lock, so a
    0.8 s budget fails on wall time and passes on CPU time."""
    outcomes: list[str] = []

    def scan() -> None:
        try:
            with regex_deadline(0.8):
                rows = tipitaka_db.search_tables_union(["t1"], {"t1": "book"}, "zzqxjk")
            outcomes.append(f"ok {len(rows)}")
        except SearchStopped as stopped:
            outcomes.append(stopped.message)

    threads = [threading.Thread(target=scan) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert outcomes == ["ok 0"] * 4
