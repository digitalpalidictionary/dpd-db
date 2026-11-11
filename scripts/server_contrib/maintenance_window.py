"""Nightly maintenance-window orchestrator for the contributor web server.

Flow (each branch logged to `logs/maintenance_YYYYMMDD.log`):

    announce the stop in the notice file, wait (only with --warn-minutes)
      → stop instances
      → capture rollback (db copy, HEAD, every delivered contributor file)
      → dirty-tree check (refuse, nothing touched)
      → git pull --ff-only + submodule update
      → reconcile (drop what main has processed or merged)
      → push the contributions branch (a failure is logged, the window goes on)
      → make sure the translation db is on disk (a failure is logged, the window goes on)
      → rebuild the db only if HEAD differs from `logs/last_built_commit`
           rebuild → generate → health check → re-apply WAL
           then restore the tracked files the build rewrote
      on ANY failure after the pull: restore db, HEAD and contributor files
    start instances (always, in a finally)
      → remove the notice file

A failed dirty-tree check or pull skips reconcile, push and rebuild. A failed
rebuild restores the contributor files too, so the overlay matches the old db
and an accepted word is not lost for a night.

The heavy steps are injectable so the whole flow can be dry-run locally against
a scratch setup without a real 2 GB rebuild.
"""

import argparse
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from scripts.server_contrib.contrib_push import push_contributions
from scripts.server_contrib.contrib_reconcile import reconcile_all
from tools.contrib_entry import delivered_files
from tools.contrib_notice import NOTICE_FILE, remove_notice, write_notice

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
    worktree: Path
    log_dir: Path
    instances: list[str] = field(default_factory=list)
    use_systemd: bool = True
    remote: str = "origin"
    branch: str = "main"
    push: bool = True
    # Where the browser-readable outcome goes. Defaults to the log folder,
    # which only root can read; nginx needs a path it can reach.
    status_file: Path | None = None
    # Minutes between the announcement and the stop. 0 = no notice, no wait.
    warn_minutes: int = 0
    notice_file: Path = NOTICE_FILE


@dataclass
class WindowSteps:
    pull: Callable[[WindowConfig], None]
    push: Callable[[WindowConfig], str]
    rebuild: Callable[[WindowConfig], None]
    generate: Callable[[WindowConfig], None]
    health_check: Callable[[WindowConfig], None]
    translation_db: Callable[[WindowConfig], None]
    wait: Callable[[float], None] = time.sleep


@dataclass
class Rollback:
    db_backup: Path | None
    pre_commit: str | None
    data_backup: Path


# Long enough for a full db rebuild step; short enough that a hung git/network
# call can't strand the window with instances stopped.
STEP_TIMEOUT = 3600
LAST_BUILT_FILE = "last_built_commit"

# The editors read the notice every 15 s (TICK_SECONDS in gui2/server_lifecycle.py)
# and need about 3 s to flush the move to the offline page, and they only move
# once the stop time has passed. The stop must come after both, or the process
# dies before any editor sees the stop time.
OFFLINE_GRACE_SECONDS = 25

# The browser-readable failure surface: one small text file the window rewrites
# at the end of every run, served at /status behind the maintainer's login.
# Written as a copy-and-replace so a reader never sees a half-written file.
STATUS_FILE = "status.txt"
STATUS_SECTIONS = ("error", "warning")
GIT_TIMEOUT = 300


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True, timeout=STEP_TIMEOUT)


def _default_pull(config: WindowConfig) -> None:
    _run(
        ["git", "pull", "--ff-only", config.remote, config.branch],
        config.project_root,
    )
    # No --init: the server inits only the submodules it needs (server_setup.sh);
    # --init would fetch all eleven.
    _run(
        ["git", "submodule", "update", "--recursive"],
        config.project_root,
    )


def _default_push(config: WindowConfig) -> str:
    result = push_contributions(
        config.project_root, config.data_dir, config.worktree, remote=config.remote
    )
    return result.message


def _default_rebuild(config: WindowConfig) -> None:
    _run(["uv", "run", "scripts/build/db_rebuild_from_tsv.py"], config.project_root)


def _default_generate(config: WindowConfig) -> None:
    # Lean gui2-only subset of generate_components (see the module docstring in
    # scripts/server_contrib/generate_components_server.py); the row-count health check
    # below is the post-rebuild gate, not pytest.
    _run(
        ["uv", "run", "scripts/server_contrib/generate_components_server.py"],
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


def _default_translation_db(config: WindowConfig) -> None:
    _run(
        ["uv", "run", "scripts/server_contrib/ensure_translation_db.py"],
        config.project_root,
    )


def default_steps() -> WindowSteps:
    return WindowSteps(
        pull=_default_pull,
        push=_default_push,
        rebuild=_default_rebuild,
        generate=_default_generate,
        health_check=_default_health_check,
        translation_db=_default_translation_db,
    )


def _make_logger(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"maintenance_{datetime.now().strftime('%Y%m%d')}.log"
    logger = logging.getLogger(f"maintenance_window.{log_path}")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    logger.addHandler(handler)
    # After addHandler, not before: pyglossary (imported by some tests) installs
    # a logger class whose addHandler replaces the handler's formatter.
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.propagate = False
    return logger


def _write_status(config: WindowConfig, outcome: Outcome, log: logging.Logger) -> None:
    """Rewrite the status file with this run's outcome and its problems.

    Read from the log rather than kept in memory, so the file cannot disagree
    with what an operator greps — but only from THIS run: the day's log also
    holds earlier runs, and their errors must not make a clean run look dirty.
    A failure to write the file must never fail the window: the run itself
    already succeeded or failed on its own.
    """
    try:
        started = datetime.now()
        log_path = config.log_dir / f"maintenance_{started.strftime('%Y%m%d')}.log"
        lines_in_log = log_path.read_text(encoding="utf-8").splitlines()
        start = 0
        for index, line in enumerate(lines_in_log):
            if line.endswith("INFO maintenance window start"):
                start = index
        problems = [
            line.strip()
            for line in lines_in_log[start:]
            if any(f" {section.upper()} " in line for section in STATUS_SECTIONS)
        ]
        head = _git_head(config.project_root)
        lines = [
            f"outcome: {outcome.value}",
            f"finished: {started.strftime('%Y-%m-%d %H:%M:%S')}",
            f"commit: {head}",
            f"problems: {len(problems)}",
            *problems,
        ]
        target = config.status_file or (config.log_dir / STATUS_FILE)
        temp = target.with_suffix(".tmp")
        temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temp.replace(target)
    except Exception as exc:  # never mask the window's own outcome
        log.error(f"could not write the status file: {exc}")


def _systemctl(
    action: str, instances: list[str], config: WindowConfig, log: logging.Logger
) -> list[str]:
    """Run `systemctl <action>` per unit. Returns the units that failed."""
    if not config.use_systemd:
        log.info(f"[--no-systemd] would {action} instances: {instances}")
        return []
    failed: list[str] = []
    for unit in instances:
        try:
            result = subprocess.run(
                ["systemctl", action, unit], check=False, timeout=GIT_TIMEOUT
            )
        except (subprocess.TimeoutExpired, OSError) as exc:
            # One hung unit must not leave the later units unattempted.
            log.error(f"systemctl {action} {unit} FAILED ({exc})")
            failed.append(unit)
            continue
        if result.returncode != 0:
            log.error(f"systemctl {action} {unit} FAILED (exit {result.returncode})")
            failed.append(unit)
        else:
            log.info(f"systemctl {action} {unit}")
    return failed


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


def _tracked_changes(project_root: Path) -> list[str]:
    """Names of tracked files with changes (untracked files do not count)."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=no"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=True,
        timeout=GIT_TIMEOUT,
    )
    # -z: paths are never quoted. A rename or copy entry is followed by its
    # source path as a separate field.
    names: list[str] = []
    entries = iter(result.stdout.split("\0"))
    for entry in entries:
        if not entry.strip():
            continue
        names.append(entry[3:])
        if entry[0] in "RC":
            next(entries, None)
    return names


def _capture_rollback(config: WindowConfig) -> Rollback:
    """Snapshot the state a failed window must put back: the db file, the
    pre-pull git HEAD (`git reset --hard` restores every tracked file the pull
    and the rebuild touched), and every delivered contributor file of every
    kind, so reconcile's drops can be undone.

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
    for paths in delivered_files(config.data_dir).values():
        for path in paths:
            shutil.copy2(path, data_backup / path.name)

    return Rollback(
        db_backup=db_backup,
        pre_commit=_git_head(config.project_root),
        data_backup=data_backup,
    )


def _restore_rollback(
    config: WindowConfig, rollback: Rollback, log: logging.Logger
) -> None:
    # Each step is guarded so one failure cannot skip the others. Contributor
    # files go first: they are the only copy of a contributor's work, and the
    # db and the working tree can be rebuilt.
    try:
        # Iterate the backup (ground truth), not the current dir: a contributor
        # file deleted by the failed window must still be restored.
        for backup_file in rollback.data_backup.iterdir():
            shutil.copy2(backup_file, config.data_dir / backup_file.name)
        log.info("restored contributor files")
    except Exception as exc:
        log.error(f"rollback of the contributor files FAILED: {exc}")
    try:
        if rollback.db_backup is not None and rollback.db_backup.exists():
            # Copy beside the db, then swap: a copy that fails half-way must
            # not leave a truncated dpd.db for the instances to start on.
            staged = config.db_path.with_name(config.db_path.name + ".restoring")
            shutil.copy2(rollback.db_backup, staged)
            os.replace(staged, config.db_path)
            # A -wal left by the failed rebuild would be replayed over the old db.
            for suffix in ("-wal", "-shm"):
                config.db_path.with_name(config.db_path.name + suffix).unlink(
                    missing_ok=True
                )
            log.info(f"restored db from {rollback.db_backup.name}")
    except Exception as exc:
        log.error(f"rollback of the database FAILED: {exc}")
    try:
        if rollback.pre_commit is not None:
            reset = subprocess.run(
                ["git", "reset", "--hard", rollback.pre_commit],
                cwd=config.project_root,
                check=False,
                timeout=GIT_TIMEOUT,
            )
            submodule = subprocess.run(
                ["git", "submodule", "update", "--recursive"],
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
    except Exception as exc:
        log.error(f"rollback git restore FAILED: {exc}")


def _restore_build_changes(config: WindowConfig, log: logging.Logger) -> None:
    """The lean rebuild rewrites tracked files (`db/sanskrit/root_families_sanskrit.tsv`
    every run, `CITATION.cff` on uposatha days). The tree was clean before the
    pull, so only the build changed them. Left alone, the next window's
    dirty-tree check would refuse."""
    names = _tracked_changes(config.project_root)
    if not names:
        return
    log.info(f"restoring tracked files the build changed: {names}")
    result = subprocess.run(
        ["git", "checkout", "--", *names],
        cwd=config.project_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT,
    )
    if result.returncode != 0:
        log.error(f"restoring build changes FAILED: {result.stderr.strip()}")


def _apply_wal(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    try:
        con.execute("PRAGMA journal_mode=WAL")
    finally:
        con.close()


def _remove_database_copy(config: WindowConfig, log: logging.Logger) -> None:
    """Delete the rollback copy once the run cannot need it. It is built from
    config, not from the Rollback object, which does not exist when the run
    returned early. This runs in a `finally`, so a failure is logged, never
    raised."""
    copy = config.db_path.with_name(config.db_path.name + ".prev")
    try:
        if copy.exists():
            size = copy.stat().st_size
            copy.unlink()
            log.info(f"removed {copy.name} ({size} bytes)")
    except OSError as exc:
        log.warning(f"could not remove {copy.name}: {exc}")


def run_maintenance(config: WindowConfig, steps: WindowSteps | None = None) -> Outcome:
    steps = steps or default_steps()
    log = _make_logger(config.log_dir)
    log.info("maintenance window start")
    last_built = config.log_dir / LAST_BUILT_FILE

    if config.use_systemd and not config.instances:
        log.warning("no --instance given: nothing is stopped before the window")
    stop_failed: list[str] = []
    outcome = Outcome.SKIPPED
    try:
        if config.warn_minutes > 0:
            stop_at = datetime.now(UTC) + timedelta(minutes=config.warn_minutes)
            try:
                write_notice(config.notice_file, stop_at)
                log.info(f"notice armed: stop at {stop_at.isoformat()}")
            except OSError as exc:
                log.warning(f"could not write the notice file: {exc}")
            # The wait happens even when the write failed, so the stop time stays 01:00.
            steps.wait(
                max(0.0, (stop_at - datetime.now(UTC)).total_seconds())
                + OFFLINE_GRACE_SECONDS
            )
        stop_failed = _systemctl("stop", config.instances, config, log)
        if stop_failed:
            # A running instance can still write the files the window reads.
            log.error(f"could not stop {stop_failed}, window refused")
            outcome = Outcome.FAILED
            return outcome

        dirty = _tracked_changes(config.project_root)
        if dirty:
            # No restore here: `git reset --hard` would destroy the changes.
            log.error(f"working tree is dirty, window refused: {dirty}")
            outcome = Outcome.FAILED
            return outcome

        rollback = _capture_rollback(config)

        try:
            steps.pull(config)
            log.info("pulled + submodules updated")
            remaining = reconcile_all(config.project_root, config.data_dir)
            log.info(f"reconciled: {remaining}")

            if config.push:
                try:
                    log.info(f"contrib_push: {steps.push(config)}")
                except Exception as exc:
                    log.error(f"contrib_push FAILED (window goes on): {exc}")

            try:
                steps.translation_db(config)
                log.info("translation db present")
            except Exception as exc:
                log.error(f"translation db missing (window goes on): {exc}")

            head = _git_head(config.project_root)
            if last_built.exists() and last_built.read_text().strip() == head:
                log.info(f"rebuild SKIPPED — main unchanged since {head}")
            else:
                steps.rebuild(config)
                log.info("db rebuilt from tsv")
                steps.generate(config)
                log.info("components generated")
                steps.health_check(config)
                log.info("health check passed")
                _apply_wal(config.db_path)
                log.info("WAL re-applied")
                _restore_build_changes(config, log)
                # Last, so a failure above rolls back and the next window
                # rebuilds again instead of trusting a half-finished one.
                last_built.write_text(head)
                outcome = Outcome.REBUILT
        except Exception as exc:
            log.error(f"window failed after the pull: {exc}")
            _restore_rollback(config, rollback, log)
            outcome = Outcome.FAILED
    except Exception as exc:
        # Failure before anything was mutated (rollback capture, dirty check):
        # there is nothing to restore.
        log.error(f"maintenance aborted before the pull: {exc}")
        outcome = Outcome.FAILED
    finally:
        try:
            start_failed = _systemctl("start", config.instances, config, log)
        except (subprocess.TimeoutExpired, OSError) as exc:
            log.error(f"could not start the instances: {exc}")
            start_failed = list(config.instances)
        if start_failed:
            # An editor that stayed down is a failed night, whatever the
            # rebuild did: the owner must see it in the status and exit code.
            outcome = Outcome.FAILED
        if config.warn_minutes > 0:
            try:
                if remove_notice(config.notice_file):
                    log.info("notice removed")
            except OSError as exc:
                log.warning(f"could not remove the notice file: {exc}")
        if outcome is not Outcome.FAILED:
            _remove_database_copy(config, log)
        log.info(f"maintenance window end: {outcome.value}")
        _write_status(config, outcome, log)
    return outcome


def _config_from_args(args: argparse.Namespace) -> WindowConfig:
    project_root: Path = args.project_root
    env_data_dir = os.environ.get("DPD_GUI2_DATA_DIR")
    data_dir: Path = (
        args.data_dir
        or (Path(env_data_dir) if env_data_dir else None)
        or project_root / "gui2" / "data"
    )
    return WindowConfig(
        project_root=project_root,
        db_path=args.db_path or project_root / "dpd.db",
        data_dir=data_dir,
        worktree=args.worktree
        or project_root.parent / f"{project_root.name}_contrib_worktree",
        log_dir=args.log_dir or project_root / "logs",
        status_file=args.status_file,
        warn_minutes=args.warn_minutes,
        notice_file=args.notice_file,
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
    parser.add_argument(
        "--worktree",
        type=Path,
        default=None,
        help="Git worktree for the contributions branch "
        "(default: <project-root>_contrib_worktree beside the clone).",
    )
    parser.add_argument("--log-dir", type=Path, default=None)
    parser.add_argument(
        "--status-file",
        type=Path,
        default=None,
        help="Browser-readable outcome file (default: <log-dir>/status.txt)",
    )
    parser.add_argument(
        "--warn-minutes",
        type=int,
        default=0,
        help="announce the stop to open editors this many minutes ahead (0 = no notice)",
    )
    parser.add_argument(
        "--notice-file",
        type=Path,
        default=NOTICE_FILE,
        help="where the editors read the stop time (they read the default path: change it only for tests)",
    )
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
    if outcome is Outcome.FAILED:
        sys.exit(1)


if __name__ == "__main__":
    main()
