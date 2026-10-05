"""The absorption invariant: never wipe what has not been absorbed upstream.

A nightly rebuild wipes the server's scratch db and rebuilds it from main's
TSVs. That is safe ONLY once the maintainer has processed everything previously
pushed — i.e. every contributor work file (`gui2/data/additions_*.json` /
`corrections_*.json`, excluding the `*_added` review files) in origin/main is
empty (`{}`) or absent. Otherwise the window must skip the rebuild and keep
serving yesterday's db. A skipped rebuild is a NORMAL outcome, not an error.
"""

import argparse
import json
import subprocess
from pathlib import Path

DATA_REL = "gui2/data"


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


def is_contributor_work_file(name: str) -> bool:
    """True for a per-contributor pending-work file (not a *_added review file)."""
    if not name.endswith(".json") or "_added" in name:
        return False
    return name.startswith("additions_") or name.startswith("corrections_")


def is_empty_blob(content: str) -> bool:
    """True when the blob holds no pending entries ({}, [] or blank)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return content.strip() in ("", "{}")
    return data == {} or data == []


def contributor_blobs(
    project_root: Path, ref: str, data_rel: str = DATA_REL
) -> dict[str, str]:
    """Map contributor-work-file path -> its content at `ref`.

    Fails CLOSED: a git error listing the tree or reading a blob raises, so the
    caller can refuse the rebuild. Returning an empty map on error would make
    `all_absorbed` report True and authorize a wipe of unabsorbed data — the one
    outcome the invariant exists to prevent.
    """
    listing = _git(
        project_root, "ls-tree", "-r", "--name-only", ref, "--", data_rel, check=False
    )
    if listing.returncode != 0:
        raise RuntimeError(
            f"git ls-tree {ref} failed (rc={listing.returncode}): {listing.stderr.strip()}"
        )

    blobs: dict[str, str] = {}
    for path in listing.stdout.splitlines():
        path = path.strip()
        if not path or not is_contributor_work_file(Path(path).name):
            continue
        show = _git(project_root, "show", f"{ref}:{path}", check=False)
        if show.returncode != 0:
            raise RuntimeError(
                f"git show {ref}:{path} failed (rc={show.returncode}): "
                f"{show.stderr.strip()}"
            )
        blobs[path] = show.stdout
    return blobs


def all_absorbed(blobs: dict[str, str]) -> bool:
    """Pure core: rebuild allowed iff every blob is empty."""
    return all(is_empty_blob(content) for content in blobs.values())


def blocking_files(blobs: dict[str, str]) -> list[str]:
    """Contributor files that still hold unabsorbed entries."""
    return sorted(path for path, content in blobs.items() if not is_empty_blob(content))


def absorption_allowed(
    project_root: Path,
    ref: str = "origin/main",
    remote: str = "origin",
    branch: str = "main",
    fetch: bool = True,
) -> tuple[bool, list[str]]:
    """Return (rebuild_allowed, blocking_files) for `ref`.

    Fails closed: a fetch or git-read error raises rather than reporting the
    tree as absorbed.
    """
    if fetch:
        result = _git(project_root, "fetch", remote, branch, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"git fetch {remote} {branch} failed (rc={result.returncode}): "
                f"{result.stderr.strip()}"
            )
    blobs = contributor_blobs(project_root, ref)
    return all_absorbed(blobs), blocking_files(blobs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--ref", default="origin/main")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--no-fetch", action="store_true")
    args = parser.parse_args()

    allowed, blocking = absorption_allowed(
        args.project_root, args.ref, args.remote, args.branch, fetch=not args.no_fetch
    )
    if allowed:
        print("rebuild allowed: all contributions absorbed")
    else:
        print("rebuild SKIPPED: unabsorbed contributions in " + args.ref)
        for path in blocking:
            print(f"  {path}")
    raise SystemExit(0 if allowed else 1)


if __name__ == "__main__":
    main()
