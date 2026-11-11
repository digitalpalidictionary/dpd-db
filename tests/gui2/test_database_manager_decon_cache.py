"""The decon cache refresh stays quiet on a read-only database only."""

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import gui2.database_manager as database_manager_module
from db.models import Base, Lookup
from gui2.database_manager import DatabaseManager


def _read_only_session(tmp_path: Path) -> Session:
    path = tmp_path / "ro.db"
    Base.metadata.create_all(create_engine(f"sqlite:///{path}"))
    engine = create_engine(f"sqlite:///file:{path}?mode=ro&uri=true")
    return Session(engine)


def _manager(session: Session) -> DatabaseManager:
    manager = object.__new__(DatabaseManager)
    manager.db_session = session
    return manager


def test_a_read_only_database_prints_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manager = _manager(_read_only_session(tmp_path))

    manager.get_all_decon_no_headwords()

    assert "decon cache refresh failed" not in capsys.readouterr().out
    assert manager.all_decon_no_headwords == set()


def test_any_other_failure_still_prints_and_the_session_stays_usable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _read_only_session(tmp_path)
    manager = _manager(session)

    def locked(*args: object, **kwargs: object) -> None:
        raise RuntimeError("database is locked")

    monkeypatch.setattr(
        database_manager_module, "save_decon_no_headwords_cache", locked
    )

    manager.get_all_decon_no_headwords()

    assert "decon cache refresh failed: database is locked" in capsys.readouterr().out
    assert session.query(Lookup).count() == 0


def _initialize_with_decon_probe(
    monkeypatch: pytest.MonkeyPatch, manager: DatabaseManager
) -> list[str]:
    """initialize_db with every lookup set a no-op, and the decon call
    recording that it ran."""
    calls: list[str] = []

    def noop(*args: object, **kwargs: object) -> None:
        pass

    def decon() -> None:
        calls.append("decon")
        manager.all_decon_no_headwords.add("x")

    for name in (
        "get_all_lemma_1_and_lemma_clean",
        "get_all_pos",
        "get_all_roots",
        "get_all_root_families",
        "get_all_compound_families",
        "get_all_word_families",
        "get_all_patterns",
    ):
        monkeypatch.setattr(manager, name, noop)
    monkeypatch.setattr(manager, "get_all_decon_no_headwords", decon)
    manager.all_decon_no_headwords = set()
    manager.initialize_db()
    return calls


def test_a_contributor_server_never_loads_the_decon_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DPD_GUI2_ROLE", "contributor-server")
    manager = _manager(_read_only_session(tmp_path))

    calls = _initialize_with_decon_probe(monkeypatch, manager)

    assert calls == []
    assert manager.all_decon_no_headwords == set()


def test_the_desktop_still_loads_the_decon_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DPD_GUI2_ROLE", raising=False)
    manager = _manager(_read_only_session(tmp_path))

    calls = _initialize_with_decon_probe(monkeypatch, manager)

    assert calls == ["decon"]
