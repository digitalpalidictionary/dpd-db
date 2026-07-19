"""Nightly maintenance-window orchestrator for the contributor web server.

Flow (each branch logged to `logs/maintenance_YYYYMMDD.log`):

    stop instances
      → contrib_push (per-user JSONs to the contributions branch)
      → pin ONE origin/main commit (fetch once, `git rev-parse`)
      → absorption_check against that pinned commit
         SKIP  → keep serving yesterday's db (a NORMAL outcome, not an error)
         ALLOW → capture rollback state (db copy + pre-pull HEAD + contributor
                 files/snapshots) → pull the pinned commit + submodule update
                 → db_rebuild_from_tsv → generate_components → health check
                 → contrib_reconcile → re-apply WAL
                 on ANY failure: restore EVERY captured component, log ERROR
    start instances (always, in a finally)

The pinned commit is used for BOTH the absorption check and the pull so the
window never rebuilds a moving target. The heavy steps (pull, rebuild, generate,
health_check) are injectable so the whole flow can be dry-run locally against a
scratch setup without a real 2 GB rebuild.
"""

import argparse
import logging
import shutil
import sqlite3
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from scripts.server.absorption_check import absorption_allowed
from scripts.server.contrib_push import push_contributions
from scripts.server.contrib_reconcile import contributor_files, reconcile_all

# Sanity floors for the post-rebuild health check (dpd has ~80k headwords /
# ~800k lookup rows; these are deliberately low guards against a broken build).
MIN_HEADWORDS = 50_000
MIN_LOOKUP = 400_000


class Outcome(str, Enum):
    SKIPPED = "skipped"
    REBUILT = "rebuilt"
    FAILED = "failed"


@dataclass
class WindowConfig:
    project_root: Path
    db_path: Path
    data_dir: Path
    snapshot_dir: Path
    log_dir: Path
    instances: list[str] = field(default_factory=list)
    use_systemd: bool = True
    remote: str = "origin"
    branch: str = "main"
    push: bool = True


@dataclass
class WindowSteps:
    pull: Callable[[WindowConfig, str], None]
    rebuild: Callable[[WindowConfig], None]
    generate: Callable[[WindowConfig], None]
    health_check: Callable[[WindowConfig], None]


@dataclass
class Rollback:
    db_backup: Path | None
    pre_commit: str | None
    data_backup: Path


# Long enough for a full db rebuild step; short enough that a hung git/network
# call can't strand the window with instances stopped.
STEP_TIMEOUT = 3600
GIT_TIMEOUT = 300


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, timeout=STEP_TIMEOUT)


def _default_pull(config: WindowConfig, pinned_commit: str) -> None:
    _run(["git", "merge", "--ff-only", pinned_commit], config.project_root)
    _run(
        ["git", "submodule", "update", "--init", "--recursive"],
        config.project_root,
    )


def _default_rebuild(config: WindowConfig) -> None:
    _run(["uv", "run", "scripts/build/db_rebuild_from_tsv.py"], config.project_root)


def _default_generate(config: WindowConfig) -> None:
    # Lean gui2-only subset of generate_components (see the module docstring in
    # scripts/server/generate_components_server.py); the row-count health check
    # below is the post-rebuild gate, not pytest.
    _run(
        ["uv", "run", "scripts/server/generate_components_server.py"],
        config.project_root,
    )


def _default_health_check(config: WindowConfig) -> None:
    """Open the rebuilt db and assert row counts are within sane bounds."""
    from db.db_helpers import get_db_session
    from db.models import DpdHeadword, Lookup

    db = get_db_session(config.db_path)
    try:
        headwords = db.query(DpdHeadword).count()
        lookups = db.query(Lookup).count()
    finally:
        db.close()
    if headwords < MIN_HEADWORDS:
        raise RuntimeError(
            f"health check failed: {headwords} headwords < {MIN_HEADWORDS}"
        )
    if lookups < MIN_LOOKUP:
        raise RuntimeError(f"health check failed: {lookups} lookup rows < {MIN_LOOKUP}")


def default_steps() -> WindowSteps:
    return WindowSteps(
        pull=_default_pull,
        rebuild=_default_rebuild,
        generate=_default_generate,
        health_check=_default_health_check,
    )


def _make_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"maintenance_{datetime.now().strftime('%Y%m%d')}.log"
    logger = logging.getLogger(f"maintenance_window.{log_path}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def _systemctl(
    action: str, instances: list[str], config: WindowConfig, log: logging.Logger
) -> None:
    if not config.use_systemd:
        log.info(f"[--no-systemd] would {action} instances: {instances}")
        return
    for unit in instances:
        result = subprocess.run(
            ["systemctl", action, unit], check=False, timeout=GIT_TIMEOUT
        )
        if result.returncode != 0:
            log.error(f"systemctl {action} {unit} FAILED (exit {result.returncode})")
        else:
            log.info(f"systemctl {action} {unit}")


def _git_head(project_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    return result.stdout.strip()


def _pin_commit(config: WindowConfig, log: logging.Logger) -> str:
    fetch = subprocess.run(
        ["git", "fetch", config.remote, config.branch],
        cwd=config.project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    if fetch.returncode != 0:
        log.warning(
            f"git fetch {config.remote} {config.branch} failed "
            f"(pinning possibly-stale ref): {fetch.stderr.strip()}"
        )
    result = subprocess.run(
        ["git", "rev-parse", f"{config.remote}/{config.branch}"],
        cwd=config.project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    return result.stdout.strip()


def _capture_rollback(config: WindowConfig) -> Rollback:
    """Snapshot the runtime-critical state the rebuild mutates, for restore.

    Captures the three components that determine what the server serves and the
    authoritative contributor record: the db file, the pre-pull git HEAD (which
    `git reset --hard` restores along with every TRACKED file the rebuild
    touched — code, submodules, tracked generated artifacts), and the
    contributor JSON files + `last_pushed/` snapshots.

    NOT captured: gitignored build intermediates the lean rebuild writes
    (e.g. `shared_data/changed_headwords`, `exporter/tpr/output/i2h.tsv`). They
    are safe to leave stale on a failed run — the server rebuilds with
    `[regenerate] db_rebuild = yes` (full regen, so those change-markers are not
    read incrementally) and gui2 never reads them at runtime; the next
    successful rebuild overwrites them.
    """
    db_backup: Path | None = None
    if config.db_path.exists():
        db_backup = config.db_path.with_name(config.db_path.name + ".prev")
        shutil.copy2(config.db_path, db_backup)

    data_backup = config.log_dir / "rollback_data"
    if data_backup.exists():
        shutil.rmtree(data_backup)
    data_backup.mkdir(parents=True)
    for path in contributor_files(config.data_dir):
        shutil.copy2(path, data_backup / path.name)
    if config.snapshot_dir.exists():
        shutil.copytree(config.snapshot_dir, data_backup / "last_pushed")

    return Rollback(
        db_backup=db_backup,
        pre_commit=_git_head(config.project_root),
        data_backup=data_backup,
    )


def _restore_rollback(
    config: WindowConfig, rollback: Rollback, log: logging.Logger
) -> None:
    if rollback.db_backup is not None and rollback.db_backup.exists():
        shutil.copy2(rollback.db_backup, config.db_path)
        log.info(f"restored db from {rollback.db_backup.name}")
    if rollback.pre_commit is not None:
        reset = subprocess.run(
            ["git", "reset", "--hard", rollback.pre_commit],
            cwd=config.project_root,
            check=False,
            timeout=GIT_TIMEOUT,
        )
        submodule = subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            cwd=config.project_root,
            check=False,
            timeout=STEP_TIMEOUT,
        )
        if reset.returncode != 0 or submodule.returncode != 0:
            log.error(
                "rollback git restore FAILED — working tree may be inconsistent "
                f"(reset={reset.returncode}, submodule={submodule.returncode})"
            )
        else:
            log.info(f"restored working tree to {rollback.pre_commit}")
    # Iterate the backup (ground truth), not the current dir: a contributor
    # file deleted by the failed rebuild must still be restored.
    for backup_file in rollback.data_backup.glob("*.json"):
        shutil.copy2(backup_file, config.data_dir / backup_file.name)
    restored_snapshots = rollback.data_backup / "last_pushed"
    if restored_snapshots.exists():
        if config.snapshot_dir.exists():
            shutil.rmtree(config.snapshot_dir)
        shutil.copytree(restored_snapshots, config.snapshot_dir)
    log.info("restored contributor files and snapshots")


def _apply_wal(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA journal_mode=WAL")
    finally:
        con.close()


def run_maintenance(config: WindowConfig, steps: WindowSteps | None = None) -> Outcome:
    steps = steps or default_steps()
    log = _make_logger(config.log_dir)
    log.info("maintenance window start")

    _systemctl("stop", config.instances, config, log)
    outcome = Outcome.SKIPPED
    try:
        if config.push:
            result = push_contributions(
                config.project_root,
                config.data_dir,
                config.snapshot_dir,
                remote=config.remote,
            )
            log.info(f"contrib_push: {result.message}")

        pinned = _pin_commit(config, log)
        log.info(f"pinned commit {pinned}")

        allowed, blocking = absorption_allowed(
            config.project_root,
            ref=pinned,
            remote=config.remote,
            branch=config.branch,
            fetch=False,
        )
        if not allowed:
            log.info(f"rebuild SKIPPED — unabsorbed: {blocking}")
            return Outcome.SKIPPED

        rollback = _capture_rollback(config)
        try:
            steps.pull(config, pinned)
            log.info("pulled + submodules updated")
            steps.rebuild(config)
            log.info("db rebuilt from tsv")
            steps.generate(config)
            log.info("components generated")
            steps.health_check(config)
            log.info("health check passed")
            remaining = reconcile_all(
                config.project_root, config.data_dir, config.snapshot_dir, pinned
            )
            log.info(f"reconciled: {remaining}")
            _apply_wal(config.db_path)
            log.info("WAL re-applied")
            outcome = Outcome.REBUILT
        except Exception as exc:
            log.error(f"rebuild failed: {exc}")
            _restore_rollback(config, rollback, log)
            outcome = Outcome.FAILED
    except Exception as exc:
        # Failure before the rebuild block (push / pin / absorption): nothing
        # was mutated yet, so there is no rollback to run — just record it so
        # the run isn't mislabelled "skipped" by the finally below.
        log.error(f"maintenance aborted before rebuild: {exc}")
        outcome = Outcome.FAILED
    finally:
        _systemctl("start", config.instances, config, log)
        log.info(f"maintenance window end: {outcome.value}")
    return outcome


def _config_from_args(args: argparse.Namespace) -> WindowConfig:
    project_root: Path = args.project_root
    data_dir: Path = args.data_dir or project_root / "gui2" / "data"
    return WindowConfig(
        project_root=project_root,
        db_path=args.db_path or project_root / "dpd.db",
        data_dir=data_dir,
        snapshot_dir=args.snapshot_dir or data_dir / "last_pushed",
        log_dir=args.log_dir or project_root / "logs",
        instances=args.instance or [],
        use_systemd=not args.no_systemd,
        remote=args.remote,
        branch=args.branch,
        push=not args.no_push,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--db-path", type=Path, default=None)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument("--instance", action="append", help="systemd unit (repeatable)")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument(
        "--no-systemd", action="store_true", help="log-only instance ctl"
    )
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()

    outcome = run_maintenance(_config_from_args(args))
    print(outcome.value)


if __name__ == "__main__":
    main()
