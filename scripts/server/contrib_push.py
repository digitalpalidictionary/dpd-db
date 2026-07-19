"""Push contributor JSON work files to the `contributions` branch.

Run in the nightly maintenance window (before reconcile). Stages ONLY the
per-contributor work files by explicit path (never `git add -A` — project
rule), commits on the `contributions` branch, pushes, and refreshes the
`last_pushed/` snapshots that `contrib_reconcile` reads. Idempotent: if nothing
changed since the last push it commits and pushes nothing.
"""

import argparse
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from scripts.server.contrib_reconcile import (
    contributor_files,
    load_json_dict,
    write_json_dict,
)


@dataclass
class PushResult:
    pushed: bool
    committed_files: list[str] = field(default_factory=list)
    message: str = ""


def _git(
    project_root: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=120,
        check=check,
    )


def _ensure_branch(project_root: Path, branch: str) -> None:
    """Switch to `branch`, creating it from the current HEAD if it is absent."""
    exists = _git(project_root, "rev-parse", "--verify", branch, check=False)
    if exists.returncode == 0:
        _git(project_root, "switch", branch)
    else:
        _git(project_root, "switch", "-c", branch)


def _nothing_staged(project_root: Path) -> bool:
    """True when the index holds no staged changes."""
    return (
        _git(project_root, "diff", "--cached", "--quiet", check=False).returncode == 0
    )


def build_commit_message() -> str:
    return f"contrib: submit data {datetime.now().strftime('%Y-%m-%d')}"


def write_snapshots(data_dir: Path, snapshot_dir: Path) -> None:
    """Record the current contributor files as the last-pushed baseline."""
    for path in contributor_files(data_dir):
        write_json_dict(snapshot_dir / path.name, load_json_dict(path))


def push_contributions(
    project_root: Path,
    data_dir: Path,
    snapshot_dir: Path,
    branch: str = "contributions",
    remote: str = "origin",
    ensure_branch: bool = True,
) -> PushResult:
    """Stage, commit, and push contributor files; refresh snapshots.

    Returns a PushResult. When nothing changed since the last push, no commit
    or push is made (pushed=False) and snapshots are left as-is.
    """
    if ensure_branch:
        _ensure_branch(project_root, branch)

    # Reset the index so a pre-populated stage (interrupted prior run, stray
    # process) can't sweep unrelated files into the contributor commit — we
    # commit ONLY the explicit paths added below (project rule: never git add -A).
    _git(project_root, "reset", "--quiet", check=False)

    rel_files = [
        p.relative_to(project_root).as_posix() for p in contributor_files(data_dir)
    ]
    for rel in rel_files:
        _git(project_root, "add", rel)

    if _nothing_staged(project_root):
        return PushResult(pushed=False, message="nothing to push")

    _git(project_root, "commit", "-m", build_commit_message())
    _git(project_root, "push", remote, branch)
    write_snapshots(data_dir, snapshot_dir)
    return PushResult(pushed=True, committed_files=rel_files, message="pushed")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--snapshot-dir", type=Path, default=None)
    parser.add_argument("--branch", default="contributions")
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args()

    project_root: Path = args.project_root
    data_dir: Path = args.data_dir or project_root / "gui2" / "data"
    snapshot_dir: Path = args.snapshot_dir or data_dir / "last_pushed"

    result = push_contributions(
        project_root, data_dir, snapshot_dir, args.branch, args.remote
    )
    print(result.message)


if __name__ == "__main__":
    main()
