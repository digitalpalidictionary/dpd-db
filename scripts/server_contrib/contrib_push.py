"""Push the contributor files to the `contributions` branch, from a worktree.

Run in the nightly window, after the pull and the reconcile. The server clone
stays on `main`; the branch lives in a separate git worktree, so a push never
touches the clone's own tree.

Each run resets `contributions` to the server clone's `HEAD` (the commit the
reconcile read, not a fresh `origin/main`), copies the delivered contributor
files in, commits if anything differs, and always pushes with
`--force-with-lease`. The branch then holds only the pending work. A pending
entry the contributor discarded leaves the branch on the next run.

`git fetch --prune` comes first: GitHub deletes a merged branch, and a stale
tracking ref would make every later `--force-with-lease` fail.
"""

import argparse
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from tools.contrib_entry import delivered_files

DATA_FOLDER = Path("gui2") / "data"


@dataclass
class PushResult:
    pushed: bool
    committed_files: list[str] = field(default_factory=list)
    message: str = ""


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )


def build_commit_message() -> str:
    return f"contrib: submit data {datetime.now().strftime('%Y-%m-%d')}"


def _ensure_worktree(project_root: Path, worktree: Path, sha: str) -> None:
    if (worktree / ".git").exists():
        return
    # A worktree folder deleted by hand stays registered and blocks `add`.
    _git(project_root, "worktree", "prune")
    _git(project_root, "worktree", "add", "--detach", str(worktree), sha)


def push_contributions(
    project_root: Path,
    data_dir: Path,
    worktree: Path,
    remote: str = "origin",
    branch: str = "contributions",
) -> PushResult:
    sha = _git(project_root, "rev-parse", "HEAD").stdout.strip()
    _ensure_worktree(project_root, worktree, sha)
    _git(project_root, "fetch", "--prune", remote)
    # -f: an interrupted earlier run may have left the worktree dirty.
    _git(worktree, "checkout", "-f", "-B", branch, sha)

    target = worktree / DATA_FOLDER
    target.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for paths in delivered_files(data_dir).values():
        for path in paths:
            shutil.copy2(path, target / path.name)
            copied.append((DATA_FOLDER / path.name).as_posix())

    if copied:
        _git(worktree, "add", "-f", "--", *copied)
    staged = _git(worktree, "diff", "--cached", "--name-only").stdout.split()
    if staged:
        _git(worktree, "commit", "-m", build_commit_message())

    _git(worktree, "push", "--force-with-lease", remote, branch)
    return PushResult(
        pushed=True,
        committed_files=staged,
        message=f"pushed {len(staged)} changed files" if staged else "branch reset",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--remote", default="origin")
    args = parser.parse_args()

    project_root: Path = args.project_root
    data_dir: Path = args.data_dir or project_root / "gui2" / "data"

    result = push_contributions(project_root, data_dir, args.worktree, args.remote)
    print(result.message)


if __name__ == "__main__":
    main()
