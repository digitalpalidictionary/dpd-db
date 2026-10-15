"""Tests for the ePitaka installer."""

import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

from exporter.epitaka import epitaka_exporter
from exporter.epitaka.epitaka_exporter import close_app, install


def make_db(path: Path, table: str, wal: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    if wal:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute(f"CREATE TABLE {table} (x TEXT)")
    conn.executemany(f"INSERT INTO {table} VALUES (?)", [(table,)] * 1000)
    conn.commit()
    return conn


def test_install_replaces_wal_destination(tmp_path: Path) -> None:
    out = tmp_path / "out.db"
    dest = tmp_path / "dest.db"
    make_db(out, "new_table").close()
    # The app keeps its connection open, so the old content sits in the WAL.
    app = make_db(dest, "old_table", wal=True)
    assert (tmp_path / "dest.db-wal").stat().st_size > 0

    assert install(out, dest)
    app.close()

    conn = sqlite3.connect(dest)
    tables = [n for (n,) in conn.execute("SELECT name FROM sqlite_master")]
    assert tables == ["new_table"]
    assert conn.execute("SELECT COUNT(*) FROM new_table").fetchone() == (1000,)
    assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    conn.close()


def test_install_leaves_destination_alone_without_a_source(tmp_path: Path) -> None:
    dest = tmp_path / "dest.db"
    make_db(dest, "old_table").close()

    assert not install(tmp_path / "missing.db", dest)

    conn = sqlite3.connect(dest)
    tables = [n for (n,) in conn.execute("SELECT name FROM sqlite_master")]
    assert tables == ["old_table"]
    conn.close()


def test_close_app_waits_for_exit() -> None:
    child = subprocess.Popen(["sleep", "60"])
    try:
        assert close_app([psutil.Process(child.pid)], timeout=10)
        assert child.wait(timeout=1) is not None
    finally:
        child.kill()


def test_close_app_reports_a_process_that_ignores_quit() -> None:
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "print('ready', flush=True); time.sleep(60)",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        child.stdout.readline()
        assert not close_app([psutil.Process(child.pid)], timeout=0.5)
    finally:
        child.kill()
        child.wait()


def run_main(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    running: bool = False,
    closes: bool = True,
    flag: str = "yes",
    db_name: str = "dpd-mobile.db",
    source_exists: bool = True,
    install_fails: list[str] | None = None,
) -> list[str]:
    calls: list[str] = [] if install_fails is None else install_fails
    source = tmp_path / "source.db"
    if source_exists:
        source.touch()
    monkeypatch.setattr(
        epitaka_exporter,
        "ProjectPaths",
        lambda: SimpleNamespace(dpd_mobile_db_path=source),
    )
    config = {
        ("exporter", "make_epitaka"): flag,
        ("epitaka", "db_path"): str(tmp_path / db_name),
    }
    monkeypatch.setattr(
        epitaka_exporter,
        "config_test",
        lambda section, option, value: config[(section, option)] == value,
    )
    monkeypatch.setattr(
        epitaka_exporter,
        "config_read",
        lambda section, option: config.get((section, option), ""),
    )
    monkeypatch.setattr(
        epitaka_exporter, "app_processes", lambda: ["app"] if running else []
    )

    def close(procs: list[object]) -> bool:
        calls.append("close")
        return closes

    monkeypatch.setattr(epitaka_exporter, "close_app", close)

    def fake_install(src_path: Path, dest: Path) -> bool:
        # Source and destination swapped would overwrite the fresh export.
        assert src_path == source
        assert dest == tmp_path / db_name
        calls.append("install")
        if install_fails is not None:
            raise sqlite3.OperationalError("disk full")
        return True

    monkeypatch.setattr(epitaka_exporter, "install", fake_install)
    monkeypatch.setattr(epitaka_exporter, "open_app", lambda: calls.append("open"))
    epitaka_exporter.main()
    return calls


def test_main_closes_and_reopens_a_running_app(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=True) == [
        "close",
        "install",
        "open",
    ]


def test_main_does_not_open_an_app_that_was_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path) == ["install"]


def test_main_skips_install_when_app_will_not_close(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=True, closes=False) == ["close"]


def test_main_does_nothing_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, flag="no") == []


def test_main_refuses_the_old_dictionary_file_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, db_name="dpd-dictionary.db") == []


def test_main_leaves_a_running_app_alone_when_the_source_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert run_main(monkeypatch, tmp_path, running=True, source_exists=False) == []


def test_main_reopens_the_app_when_the_copy_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[str] = []
    with pytest.raises(sqlite3.OperationalError):
        run_main(monkeypatch, tmp_path, running=True, install_fails=calls)
    assert calls == ["close", "install", "open"]
