"""run_maintenance with stub heavy steps, real git, and a bare origin."""

import json
import logging
import shutil
import sqlite3
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from scripts.server_contrib import maintenance_window
from scripts.server_contrib.contrib_reconcile import load_json_dict, write_json_dict
from scripts.server_contrib.maintenance_window import (
    OFFLINE_GRACE_SECONDS,
    Outcome,
    WindowConfig,
    WindowSteps,
    default_steps,
    run_maintenance,
)
from tools.contrib_entry import entry_hash
from tools.contrib_notice import NOTICE_FILE, read_notice


def _git(*args: str, cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def _configure(repo: Path) -> None:
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("config", "commit.gpgsign", "false", cwd=repo)


def _make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE marker (v TEXT)")
    con.execute("INSERT INTO marker VALUES ('original')")
    con.commit()
    con.close()


def _db_marker(path: Path) -> str:
    con = sqlite3.connect(path)
    try:
        return con.execute("SELECT v FROM marker").fetchone()[0]
    finally:
        con.close()


class Calls:
    """Records which stub steps ran."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def step(self, name: str, error: Exception | None = None):
        def run(config: WindowConfig) -> None:
            self.names.append(name)
            if error is not None:
                raise error

        return run

    def push_step(self, error: Exception | None = None):
        def run(config: WindowConfig) -> str:
            self.names.append("push")
            if error is not None:
                raise error
            return "ok"

        return run


def _steps(calls: Calls, **overrides) -> WindowSteps:
    real = default_steps()
    steps = WindowSteps(
        pull=real.pull,
        push=calls.push_step(),
        rebuild=calls.step("rebuild"),
        generate=calls.step("generate"),
        health_check=calls.step("health_check"),
        translation_db=lambda config: None,
    )
    for name, value in overrides.items():
        setattr(steps, name, value)
    return steps


class Setup:
    """Bare origin, a maintainer clone, and the server clone the window runs in."""

    def __init__(self, tmp_path: Path) -> None:
        bare = tmp_path / "remote.git"
        bare.mkdir()
        _git("init", "--bare", "-b", "main", cwd=bare)
        self.bare = bare

        self.maintainer = tmp_path / "maintainer"
        self.maintainer.mkdir()
        _git("init", "-b", "main", cwd=self.maintainer)
        _configure(self.maintainer)
        _git("remote", "add", "origin", bare.as_uri(), cwd=self.maintainer)
        (self.maintainer / "README").write_text("x")
        (self.maintainer / "tracked.tsv").write_text("original\n")
        self.main_commit("seed")

        self.repo = tmp_path / "server"
        _git("clone", "-q", bare.as_uri(), str(self.repo), cwd=tmp_path)
        _configure(self.repo)

        self.config = WindowConfig(
            project_root=self.repo,
            db_path=self.repo / "dpd.db",
            data_dir=tmp_path / "server_data",
            worktree=tmp_path / "worktree",
            log_dir=self.repo / "logs",
            instances=["dpd-gui@alice"],
            use_systemd=False,
        )
        self.config.data_dir.mkdir()
        _make_db(self.config.db_path)

    def main_commit(self, message: str, **files: str) -> None:
        for name, text in files.items():
            path = self.maintainer / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        _git("add", "-A", cwd=self.maintainer)
        _git("commit", "-q", "-m", message, cwd=self.maintainer)
        _git("push", "-q", "origin", "main", cwd=self.maintainer)

    def head(self) -> str:
        return _git("rev-parse", "HEAD", cwd=self.repo)

    def log_text(self) -> str:
        logs = list(self.config.log_dir.glob("maintenance_*.log"))
        assert logs, "no log written"
        return logs[0].read_text(encoding="utf-8")


def _setup(tmp_path: Path) -> Setup:
    return Setup(tmp_path)


def _entry(meaning: str) -> dict:
    return {"id": 1, "meaning_1": meaning}


class TestHappyPath:
    def test_first_window_rebuilds_pushes_and_records_the_commit(self, tmp_path: Path):
        setup = _setup(tmp_path)
        write_json_dict(
            setup.config.data_dir / "additions_alice.json", {"alice_1": _entry("a")}
        )
        steps = _steps(Calls())
        steps.push = default_steps().push  # the real push, to the bare origin

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.REBUILT
        text = setup.log_text()
        assert "health check passed" in text
        assert "WAL re-applied" in text
        assert "maintenance window end: rebuilt" in text
        assert (setup.config.log_dir / "last_built_commit").read_text() == setup.head()
        shown = _git(
            "show", "contributions:gui2/data/additions_alice.json", cwd=setup.bare
        )
        assert json.loads(shown) == {"alice_1": _entry("a")}

    def test_main_unchanged_means_no_rebuild_but_the_push_still_runs(
        self, tmp_path: Path
    ):
        setup = _setup(tmp_path)
        run_maintenance(setup.config, _steps(Calls()))
        calls = Calls()

        outcome = run_maintenance(setup.config, _steps(calls))

        assert outcome is Outcome.SKIPPED
        assert calls.names == ["push"]
        assert "rebuild SKIPPED" in setup.log_text()

    def test_main_moved_means_a_new_rebuild(self, tmp_path: Path):
        setup = _setup(tmp_path)
        run_maintenance(setup.config, _steps(Calls()))
        setup.main_commit("more", other="y")
        calls = Calls()

        outcome = run_maintenance(setup.config, _steps(calls))

        assert outcome is Outcome.REBUILT
        assert "rebuild" in calls.names

    def test_status_file_reports_a_rebuild(self, tmp_path: Path):
        setup = _setup(tmp_path)

        run_maintenance(setup.config, _steps(Calls()))

        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert status.startswith("outcome: rebuilt\n")
        assert f"commit: {setup.head()}" in status
        assert "problems: 0" in status

    def test_status_file_can_go_where_nginx_can_read_it(self, tmp_path: Path):
        setup = _setup(tmp_path)
        setup.config.status_file = tmp_path / "served" / "status.txt"
        setup.config.status_file.parent.mkdir()

        run_maintenance(setup.config, _steps(Calls()))

        assert setup.config.status_file.read_text(encoding="utf-8").startswith(
            "outcome: rebuilt\n"
        )
        assert not (setup.config.log_dir / "status.txt").exists()

    def test_status_file_ignores_an_earlier_runs_failure(self, tmp_path: Path):
        """A clean run after a failed one in the same day must not inherit its
        error: the operator reads this file to decide the night was fine."""
        setup = _setup(tmp_path)
        broken = _steps(Calls(), rebuild=Calls().step("rebuild", RuntimeError("boom")))
        assert run_maintenance(setup.config, broken) is Outcome.FAILED

        run_maintenance(setup.config, _steps(Calls()))

        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert status.startswith("outcome: rebuilt\n")
        assert "problems: 0" in status
        assert "boom" not in status

    def test_status_file_reports_a_failure_and_its_reason(self, tmp_path: Path):
        setup = _setup(tmp_path)
        steps = _steps(Calls(), rebuild=Calls().step("rebuild", RuntimeError("boom")))

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.FAILED
        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert status.startswith("outcome: failed\n")
        assert "problems: 1" in status
        assert "boom" in status

    def test_processed_entries_are_dropped_after_the_pull(self, tmp_path: Path):
        setup = _setup(tmp_path)
        kept, done = _entry("kept"), _entry("done")
        write_json_dict(
            setup.config.data_dir / "additions_alice.json",
            {"alice_1": done, "alice_2": kept},
        )
        log = [{"_source_key": "alice_1", "_source_hash": entry_hash(done)}]
        setup.main_commit(
            "processed", **{"gui2/data/additions_added.json": json.dumps(log)}
        )

        run_maintenance(setup.config, _steps(Calls()))

        assert load_json_dict(setup.config.data_dir / "additions_alice.json") == {
            "alice_2": kept
        }


class TestRefusedAndFailedBeforeTheRebuild:
    def test_dirty_tree_refuses_everything_and_keeps_the_change(self, tmp_path: Path):
        setup = _setup(tmp_path)
        (setup.repo / "tracked.tsv").write_text("hand edit\n")
        setup.main_commit("moved", other="y")
        calls = Calls()
        pulled: list[str] = []
        steps = _steps(calls, pull=lambda c: pulled.append("pull"))

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.FAILED
        assert pulled == [] and calls.names == []
        assert (setup.repo / "tracked.tsv").read_text() == "hand edit\n"
        text = setup.log_text()
        assert "tracked.tsv" in text
        assert "would start instances" in text

    def test_pull_failure_skips_reconcile_push_and_rebuild(self, tmp_path: Path):
        setup = _setup(tmp_path)
        done = _entry("done")
        write_json_dict(
            setup.config.data_dir / "additions_alice.json", {"alice_1": done}
        )
        log = [{"_source_key": "alice_1", "_source_hash": entry_hash(done)}]
        setup.main_commit("log", **{"gui2/data/additions_added.json": json.dumps(log)})
        calls = Calls()

        def failing_pull(config: WindowConfig) -> None:
            raise RuntimeError("network down")

        outcome = run_maintenance(setup.config, _steps(calls, pull=failing_pull))

        assert outcome is Outcome.FAILED
        assert calls.names == []
        assert load_json_dict(setup.config.data_dir / "additions_alice.json") == {
            "alice_1": done
        }
        assert "would start instances" in setup.log_text()


class TestRollback:
    def test_failed_rebuild_restores_db_head_and_contributor_files(
        self, tmp_path: Path
    ):
        setup = _setup(tmp_path)
        done = _entry("done")
        path = setup.config.data_dir / "additions_alice.json"
        write_json_dict(path, {"alice_1": done})
        (setup.config.data_dir / "checked_alice.csv").write_text("word\n")
        before = setup.head()
        log = [{"_source_key": "alice_1", "_source_hash": entry_hash(done)}]
        setup.main_commit("log", **{"gui2/data/additions_added.json": json.dumps(log)})

        def corrupting_rebuild(config: WindowConfig) -> None:
            config.db_path.write_bytes(b"CORRUPT")
            (config.data_dir / "checked_alice.csv").unlink()
            raise RuntimeError("rebuild blew up")

        outcome = run_maintenance(
            setup.config, _steps(Calls(), rebuild=corrupting_rebuild)
        )

        assert outcome is Outcome.FAILED
        assert _db_marker(setup.config.db_path) == "original"
        assert setup.head() == before
        assert load_json_dict(path) == {"alice_1": done}
        assert (setup.config.data_dir / "checked_alice.csv").read_text() == "word\n"
        assert not (setup.config.log_dir / "last_built_commit").exists()
        text = setup.log_text()
        assert "rebuild blew up" in text
        assert "would start instances" in text

    def test_a_failed_db_restore_still_restores_the_contributor_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        setup = _setup(tmp_path)
        done = _entry("done")
        path = setup.config.data_dir / "additions_alice.json"
        write_json_dict(path, {"alice_1": done})
        (setup.config.data_dir / "checked_alice.csv").write_text("word\n")
        before = setup.head()
        log = [{"_source_key": "alice_1", "_source_hash": entry_hash(done)}]
        setup.main_commit("log", **{"gui2/data/additions_added.json": json.dumps(log)})

        real_copy2 = shutil.copy2

        def failing_copy2(src, dst, *args, **kwargs):
            if str(src).endswith(".prev"):
                raise OSError("disk full")
            return real_copy2(src, dst, *args, **kwargs)

        def corrupting_rebuild(config: WindowConfig) -> None:
            config.db_path.write_bytes(b"CORRUPT")
            (config.data_dir / "checked_alice.csv").unlink()
            monkeypatch.setattr(
                "scripts.server_contrib.maintenance_window.shutil.copy2",
                failing_copy2,
            )
            raise RuntimeError("rebuild blew up")

        outcome = run_maintenance(
            setup.config, _steps(Calls(), rebuild=corrupting_rebuild)
        )

        assert outcome is Outcome.FAILED
        assert load_json_dict(path) == {"alice_1": done}
        assert (setup.config.data_dir / "checked_alice.csv").read_text() == "word\n"
        assert setup.head() == before
        text = setup.log_text()
        assert "rollback of the database FAILED" in text
        assert "maintenance aborted before the pull" not in text

    def test_push_failure_is_logged_and_the_rebuild_still_runs(self, tmp_path: Path):
        setup = _setup(tmp_path)
        calls = Calls()
        steps = _steps(calls, push=calls.push_step(RuntimeError("no remote")))

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.REBUILT
        assert calls.names == ["push", "rebuild", "generate", "health_check"]
        assert "contrib_push FAILED" in setup.log_text()


class TestBuildLeftovers:
    def test_tracked_files_the_build_rewrote_are_restored(self, tmp_path: Path):
        setup = _setup(tmp_path)

        def rewriting_rebuild(config: WindowConfig) -> None:
            (config.project_root / "tracked.tsv").write_text("rebuilt\n")

        outcome = run_maintenance(
            setup.config, _steps(Calls(), rebuild=rewriting_rebuild)
        )

        assert outcome is Outcome.REBUILT
        assert (setup.repo / "tracked.tsv").read_text() == "original\n"
        assert "tracked.tsv" in setup.log_text()
        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.SKIPPED


class TestInstanceControl:
    def test_no_systemd_logs_only(self, tmp_path: Path):
        setup = _setup(tmp_path)

        run_maintenance(setup.config, _steps(Calls()))

        text = setup.log_text()
        assert "would stop instances" in text
        assert "would start instances" in text


class TestStopFailure:
    def test_a_failed_stop_refuses_the_window_and_still_restarts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        setup = _setup(tmp_path)
        setup.config.use_systemd = True
        calls = Calls()
        seen: list[str] = []

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            seen.append(" ".join(cmd))
            return subprocess.CompletedProcess(cmd, 1 if cmd[1] == "stop" else 0)

        monkeypatch.setattr(
            "scripts.server_contrib.maintenance_window.subprocess.run", fake_run
        )

        outcome = run_maintenance(setup.config, _steps(calls))

        assert outcome is Outcome.FAILED
        assert calls.names == []
        assert "systemctl start dpd-gui@alice" in seen
        assert "window refused" in setup.log_text()

    def test_a_failed_start_fails_the_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        setup = _setup(tmp_path)
        setup.config.use_systemd = True
        calls = Calls()
        seen: list[str] = []

        real_run = subprocess.run

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            if cmd[0] != "systemctl":
                return real_run(cmd, **kwargs)  # pyright: ignore[reportCallIssue, reportArgumentType]
            seen.append(" ".join(cmd))
            return subprocess.CompletedProcess(cmd, 1 if cmd[1] == "start" else 0)

        monkeypatch.setattr(
            "scripts.server_contrib.maintenance_window.subprocess.run", fake_run
        )

        outcome = run_maintenance(setup.config, _steps(calls))

        assert outcome is Outcome.FAILED
        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert status.startswith("outcome: failed\n")

    def test_a_start_that_times_out_fails_the_run_and_writes_the_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        setup = _setup(tmp_path)
        setup.config.use_systemd = True
        calls = Calls()

        real_run = subprocess.run

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            if cmd[0] != "systemctl":
                return real_run(cmd, **kwargs)  # pyright: ignore[reportCallIssue, reportArgumentType]
            if cmd[1] == "start":
                raise subprocess.TimeoutExpired(cmd, 300)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr(
            "scripts.server_contrib.maintenance_window.subprocess.run", fake_run
        )

        outcome = run_maintenance(setup.config, _steps(calls))

        assert outcome is Outcome.FAILED
        assert (setup.config.log_dir / "status.txt").exists()

    def test_a_timed_out_start_does_not_skip_the_other_instances(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        setup = _setup(tmp_path)
        setup.config.use_systemd = True
        setup.config.instances = ["dpd-gui@alice", "dpd-gui@bob"]
        seen: list[str] = []

        real_run = subprocess.run

        def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            if cmd[0] != "systemctl":
                return real_run(cmd, **kwargs)  # pyright: ignore[reportCallIssue, reportArgumentType]
            seen.append(" ".join(cmd))
            if cmd[1] == "start" and cmd[2] == "dpd-gui@alice":
                raise subprocess.TimeoutExpired(cmd, 300)
            return subprocess.CompletedProcess(cmd, 0)

        monkeypatch.setattr(
            "scripts.server_contrib.maintenance_window.subprocess.run", fake_run
        )

        outcome = run_maintenance(setup.config, _steps(Calls()))

        assert outcome is Outcome.FAILED
        assert "systemctl start dpd-gui@bob" in seen


class TestRollbackWal:
    def test_a_wal_left_by_the_failed_rebuild_is_removed(self, tmp_path: Path):
        setup = _setup(tmp_path)

        def rebuild_leaves_wal(config: WindowConfig) -> None:
            (config.db_path.parent / "dpd.db-wal").write_bytes(b"stale")
            raise RuntimeError("boom")

        outcome = run_maintenance(
            setup.config, _steps(Calls(), rebuild=rebuild_leaves_wal)
        )

        assert outcome is Outcome.FAILED
        assert not (setup.repo / "dpd.db-wal").exists()
        assert _db_marker(setup.config.db_path) == "original"


def test_pull_and_rollback_never_init_new_submodules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.server_contrib import maintenance_window as mw

    seen: list[list[str]] = []
    monkeypatch.setattr(mw, "_run", lambda cmd, cwd: seen.append(cmd))
    setup = _setup(tmp_path)
    mw._default_pull(setup.config)
    assert ["git", "submodule", "update", "--recursive"] in seen
    assert not any("--init" in cmd for cmd in seen)

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(mw.subprocess, "run", fake_run)
    backup = tmp_path / "rollback_data"
    backup.mkdir()
    mw._restore_rollback(
        setup.config,
        mw.Rollback(db_backup=None, pre_commit="abc", data_backup=backup),
        mw._make_logger(setup.config.log_dir),
    )
    submodule_calls = [c for c in calls if c[:2] == ["git", "submodule"]]
    assert submodule_calls == [["git", "submodule", "update", "--recursive"]]


@pytest.mark.parametrize(
    ("outcome", "code"),
    [(Outcome.FAILED, 1), (Outcome.SKIPPED, None), (Outcome.REBUILT, None)],
)
def test_main_exits_1_only_when_the_window_failed(
    monkeypatch: pytest.MonkeyPatch, outcome: Outcome, code: int | None
) -> None:
    from scripts.server_contrib import maintenance_window as mw

    monkeypatch.setattr(mw, "run_maintenance", lambda config: outcome)
    monkeypatch.setattr("sys.argv", ["maintenance_window.py", "--no-systemd"])
    if code is None:
        mw.main()
    else:
        with pytest.raises(SystemExit) as exc:
            mw.main()
        assert exc.value.code == code


def _prev(setup: Setup) -> Path:
    return setup.config.db_path.with_name("dpd.db.prev")


class TestDatabaseCopyCleanup:
    def test_a_rebuilt_run_removes_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.REBUILT

        assert not _prev(setup).exists()

    def test_a_skipped_run_removes_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)
        run_maintenance(setup.config, _steps(Calls()))

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.SKIPPED

        assert not _prev(setup).exists()

    def test_a_failed_run_keeps_the_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)
        broken = _steps(Calls(), rebuild=Calls().step("rebuild", RuntimeError("boom")))

        assert run_maintenance(setup.config, broken) is Outcome.FAILED

        assert _prev(setup).exists()

    def test_a_refused_run_deletes_nothing(self, tmp_path: Path):
        setup = _setup(tmp_path)
        _prev(setup).write_bytes(b"older copy")
        (setup.repo / "tracked.tsv").write_text("hand edit\n")

        assert run_maintenance(setup.config, _steps(Calls())) is Outcome.FAILED

        assert _prev(setup).read_bytes() == b"older copy"

    def test_the_log_names_the_deleted_copy(self, tmp_path: Path):
        setup = _setup(tmp_path)

        run_maintenance(setup.config, _steps(Calls()))

        assert "removed dpd.db.prev" in setup.log_text()


class TestTranslationDb:
    def test_the_step_runs_every_window_and_is_logged(self, tmp_path: Path):
        setup = _setup(tmp_path)
        calls = Calls()
        steps = _steps(calls, translation_db=calls.step("translation_db"))

        run_maintenance(setup.config, steps)
        run_maintenance(
            setup.config,
            _steps(Calls(), translation_db=calls.step("translation_db")),
        )

        assert calls.names.count("translation_db") == 2
        assert "translation db present" in setup.log_text()

    def test_a_failure_is_logged_and_the_window_goes_on(self, tmp_path: Path):
        setup = _setup(tmp_path)
        calls = Calls()
        steps = _steps(
            calls,
            translation_db=Calls().step("translation_db", RuntimeError("no network")),
        )

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.REBUILT
        assert "rebuild" in calls.names
        assert "translation db missing (window goes on): no network" in setup.log_text()
        status = (setup.config.log_dir / "status.txt").read_text(encoding="utf-8")
        assert "problems: 1" in status
        assert "translation db missing" in status


class _FormatSwappingLogger(logging.Logger):
    """Behaves like pyglossary's logger class: adding a handler replaces its
    formatter."""

    def addHandler(self, hdlr: logging.Handler) -> None:
        super().addHandler(hdlr)
        hdlr.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))


class TestLogFormat:
    def test_the_format_survives_a_logger_class_that_swaps_formatters(
        self, tmp_path: Path
    ):
        previous = logging.getLoggerClass()
        logging.setLoggerClass(_FormatSwappingLogger)
        try:
            log = maintenance_window._make_logger(tmp_path / "logs")
            log.error("boom")
        finally:
            logging.setLoggerClass(previous)

        text = next((tmp_path / "logs").glob("maintenance_*.log")).read_text(
            encoding="utf-8"
        )

        assert " ERROR boom" in text


class TestWarning:
    def _warn_setup(self, tmp_path: Path, minutes: int = 30) -> Setup:
        setup = _setup(tmp_path)
        setup.config.warn_minutes = minutes
        setup.config.notice_file = tmp_path / "notice.json"
        return setup

    def test_notice_is_armed_then_waited_on_then_removed(self, tmp_path: Path):
        setup = self._warn_setup(tmp_path)
        seen: dict = {}
        order: list[str] = []

        def fake_wait(seconds: float) -> None:
            seen["seconds"] = seconds
            seen["notice"] = read_notice(setup.config.notice_file)
            order.append("wait")

        calls = Calls()
        steps = _steps(calls, wait=fake_wait)
        real_pull = steps.pull
        steps.pull = lambda config: (order.append("pull"), real_pull(config))[1]

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.REBUILT
        grace = OFFLINE_GRACE_SECONDS
        assert 1790 + grace <= seen["seconds"] <= 1800 + grace
        stop_at, reason = seen["notice"]
        assert reason == "ok" and stop_at is not None
        ahead = stop_at - datetime.now(UTC)
        assert timedelta(minutes=29) < ahead < timedelta(minutes=30, seconds=1)
        assert order == ["wait", "pull"]
        assert not setup.config.notice_file.exists()
        text = setup.log_text()
        assert "notice armed" in text
        assert "notice removed" in text
        assert text.index("notice armed") < text.index("pulled + submodules")

    def test_the_stop_waits_for_the_notice(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        setup = self._warn_setup(tmp_path)
        setup.config.use_systemd = True
        events: list[str] = []
        real_run = subprocess.run

        def fake_run(cmd, *args, **kwargs):
            if cmd[0] == "systemctl":
                events.append(f"systemctl {cmd[1]}")
                return subprocess.CompletedProcess(cmd, 0)
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", fake_run)
        steps = _steps(Calls(), wait=lambda seconds: events.append("wait"))

        run_maintenance(setup.config, steps)

        assert events == ["wait", "systemctl stop", "systemctl start"]

    def test_warn_zero_never_waits_and_writes_nothing(self, tmp_path: Path):
        setup = self._warn_setup(tmp_path, minutes=0)
        waited: list[float] = []

        outcome = run_maintenance(setup.config, _steps(Calls(), wait=waited.append))

        assert outcome is Outcome.REBUILT
        assert waited == []
        assert not setup.config.notice_file.exists()
        assert "notice" not in setup.log_text()

    def test_an_unwritable_notice_path_does_not_fail_the_window(self, tmp_path: Path):
        setup = self._warn_setup(tmp_path)
        blocker = tmp_path / "a_file"
        blocker.write_text("x")
        setup.config.notice_file = blocker / "notice.json"
        waited: list[float] = []

        outcome = run_maintenance(setup.config, _steps(Calls(), wait=waited.append))

        assert outcome is Outcome.REBUILT
        assert len(waited) == 1
        assert 1790 + OFFLINE_GRACE_SECONDS <= waited[0] <= 1800 + OFFLINE_GRACE_SECONDS
        text = setup.log_text()
        assert "could not write the notice file" in text
        assert "notice armed" not in text

    def test_a_failed_pull_still_removes_the_notice(self, tmp_path: Path):
        setup = self._warn_setup(tmp_path)
        waited: list[float] = []
        steps = _steps(Calls(), wait=waited.append)
        steps.pull = Calls().step("pull", error=RuntimeError("network"))

        outcome = run_maintenance(setup.config, steps)

        assert outcome is Outcome.FAILED
        assert len(waited) == 1
        assert not setup.config.notice_file.exists()
        text = setup.log_text()
        assert "notice removed" in text
        assert text.index("notice armed") < text.index("window failed after the pull")

    def test_the_command_line_flags_reach_the_window(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        seen: list[WindowConfig] = []

        def fake_run(config: WindowConfig) -> Outcome:
            seen.append(config)
            return Outcome.SKIPPED

        monkeypatch.setattr(maintenance_window, "run_maintenance", fake_run)
        monkeypatch.setattr(
            "sys.argv",
            [
                "maintenance_window.py",
                "--no-systemd",
                "--warn-minutes",
                "5",
                "--notice-file",
                str(tmp_path / "x.json"),
            ],
        )

        maintenance_window.main()

        assert seen[0].warn_minutes == 5
        assert seen[0].notice_file == tmp_path / "x.json"

    def test_without_the_flags_there_is_no_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        seen: list[WindowConfig] = []

        def fake_run(config: WindowConfig) -> Outcome:
            seen.append(config)
            return Outcome.SKIPPED

        monkeypatch.setattr(maintenance_window, "run_maintenance", fake_run)
        monkeypatch.setattr("sys.argv", ["maintenance_window.py", "--no-systemd"])

        maintenance_window.main()

        assert seen[0].warn_minutes == 0
        assert seen[0].notice_file == NOTICE_FILE

    def test_arguments_reach_the_config(self, tmp_path: Path):
        import argparse

        args = argparse.Namespace(
            project_root=tmp_path,
            db_path=None,
            data_dir=tmp_path / "d",
            worktree=None,
            log_dir=None,
            status_file=None,
            instance=None,
            no_systemd=True,
            remote="origin",
            branch="main",
            no_push=True,
            warn_minutes=5,
            notice_file=tmp_path / "x.json",
        )

        config = maintenance_window._config_from_args(args)

        assert config.warn_minutes == 5
        assert config.notice_file == tmp_path / "x.json"
