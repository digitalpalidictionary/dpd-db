"""run_maintenance with stub heavy steps, real git, and a bare origin."""

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from scripts.server_contrib.contrib_reconcile import load_json_dict, write_json_dict
from scripts.server_contrib.maintenance_window import (
    Outcome,
    WindowConfig,
    WindowSteps,
    default_steps,
    run_maintenance,
)
from tools.contrib_entry import entry_hash


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
