import json
import sqlite3
import subprocess
from pathlib import Path

from scripts.server.contrib_reconcile import load_json_dict, write_json_dict
from scripts.server.maintenance_window import (
    Outcome,
    WindowConfig,
    WindowSteps,
    run_maintenance,
)


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE marker (v TEXT)")
    con.execute("INSERT INTO marker VALUES ('original')")
    con.commit()
    con.close()


def _setup(tmp_path: Path) -> WindowConfig:
    """Scratch repo + bare remote (origin/main), a fake db, one work file."""
    bare = tmp_path / "remote.git"
    bare.mkdir()
    _git("init", "--bare", "-b", "main", cwd=bare)

    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-b", "main", cwd=repo)
    _git("config", "user.email", "t@t.t", cwd=repo)
    _git("config", "user.name", "t", cwd=repo)
    _git("remote", "add", "origin", str(bare), cwd=repo)
    (repo / "README").write_text("x", encoding="utf-8")
    _git("add", "README", cwd=repo)
    _git("commit", "-m", "seed", cwd=repo)
    _git("push", "origin", "main", cwd=repo)

    data_dir = repo / "gui2" / "data"
    data_dir.mkdir(parents=True)
    snapshot_dir = data_dir / "last_pushed"
    snapshot_dir.mkdir()

    db_path = repo / "dpd.db"
    _make_db(db_path)

    return WindowConfig(
        project_root=repo,
        db_path=db_path,
        data_dir=data_dir,
        snapshot_dir=snapshot_dir,
        log_dir=repo / "logs",
        instances=["dpd-gui@alice"],
        use_systemd=False,
        push=False,
    )


def _ok_steps() -> WindowSteps:
    return WindowSteps(
        pull=lambda c, pin: None,
        rebuild=lambda c: None,
        generate=lambda c: None,
        health_check=lambda c: None,
    )


def _log_text(config: WindowConfig) -> str:
    logs = list(config.log_dir.glob("maintenance_*.log"))
    assert logs, "no log written"
    return logs[0].read_text(encoding="utf-8")


class TestHappyPath:
    def test_rebuild_when_absorbed(self, tmp_path: Path):
        config = _setup(tmp_path)
        # origin/main has NO contributor files -> absorbed -> rebuild allowed.
        write_json_dict(
            config.data_dir / "additions_alice.json", {"alice_1": {"id": 1}}
        )

        outcome = run_maintenance(config, _ok_steps())

        assert outcome is Outcome.REBUILT
        text = _log_text(config)
        assert "health check passed" in text
        assert "WAL re-applied" in text
        assert "maintenance window end: rebuilt" in text


class TestSkipPath:
    def test_skip_when_unabsorbed(self, tmp_path: Path):
        config = _setup(tmp_path)
        # Put a NON-EMPTY contributor file on origin/main -> not absorbed.
        pending = config.data_dir / "additions_alice.json"
        pending.write_text(json.dumps({"alice_1": {"id": 1}}), encoding="utf-8")
        _git("add", "gui2/data/additions_alice.json", cwd=config.project_root)
        _git("commit", "-m", "pending", cwd=config.project_root)
        _git("push", "origin", "main", cwd=config.project_root)

        outcome = run_maintenance(config, _ok_steps())

        assert outcome is Outcome.SKIPPED
        text = _log_text(config)
        assert "rebuild SKIPPED" in text
        assert "maintenance window end: skipped" in text


class TestRollbackPath:
    def test_failure_restores_everything(self, tmp_path: Path):
        config = _setup(tmp_path)
        work = {"alice_1": {"id": 1, "meaning_1": "original"}}
        write_json_dict(config.data_dir / "additions_alice.json", work)
        write_json_dict(config.snapshot_dir / "additions_alice.json", work)

        def corrupting_rebuild(c: WindowConfig) -> None:
            # Simulate a rebuild that mutates the db and a contributor file
            # before the health check fails.
            c.db_path.write_bytes(b"CORRUPT")
            (c.data_dir / "additions_alice.json").write_text("{}", encoding="utf-8")

        def failing_health(c: WindowConfig) -> None:
            raise RuntimeError("boom")

        steps = WindowSteps(
            pull=lambda c, pin: None,
            rebuild=corrupting_rebuild,
            generate=lambda c: None,
            health_check=failing_health,
        )

        outcome = run_maintenance(config, steps)

        assert outcome is Outcome.FAILED
        # db restored to the original valid sqlite (not the CORRUPT bytes).
        con = sqlite3.connect(config.db_path)
        assert con.execute("SELECT v FROM marker").fetchone()[0] == "original"
        con.close()
        # contributor file restored to its pre-rebuild content.
        assert load_json_dict(config.data_dir / "additions_alice.json") == work
        text = _log_text(config)
        assert "rebuild failed: boom" in text
        assert "restored db from dpd.db.prev" in text
        assert "maintenance window end: failed" in text

    def test_deleted_contributor_file_is_restored(self, tmp_path: Path):
        config = _setup(tmp_path)
        work = {"alice_1": {"id": 1, "meaning_1": "original"}}
        write_json_dict(config.data_dir / "additions_alice.json", work)
        write_json_dict(config.snapshot_dir / "additions_alice.json", work)

        def deleting_rebuild(c: WindowConfig) -> None:
            # A rebuild that DELETES a contributor file (not just edits it):
            # restore must iterate the backup, not the current dir.
            (c.data_dir / "additions_alice.json").unlink()

        steps = WindowSteps(
            pull=lambda c, pin: None,
            rebuild=deleting_rebuild,
            generate=lambda c: None,
            health_check=lambda c: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        outcome = run_maintenance(config, steps)

        assert outcome is Outcome.FAILED
        assert load_json_dict(config.data_dir / "additions_alice.json") == work


class TestPrePushFailure:
    def test_abort_before_rebuild_logs_failed(self, tmp_path: Path):
        config = _setup(tmp_path)
        config.push = True
        # No remote configured for pushing on a bare-add scenario would raise;
        # instead force _pin_commit to fail by pointing at a bad remote.
        config.remote = "no_such_remote"
        write_json_dict(
            config.data_dir / "additions_alice.json", {"alice_1": {"id": 1}}
        )

        outcome = run_maintenance(config, _ok_steps())

        assert outcome is Outcome.FAILED
        text = _log_text(config)
        assert "maintenance aborted before rebuild" in text
        assert "maintenance window end: failed" in text


class TestInstanceControl:
    def test_no_systemd_logs_only(self, tmp_path: Path):
        config = _setup(tmp_path)
        run_maintenance(config, _ok_steps())
        text = _log_text(config)
        assert "[--no-systemd] would stop instances" in text
        assert "[--no-systemd] would start instances" in text
