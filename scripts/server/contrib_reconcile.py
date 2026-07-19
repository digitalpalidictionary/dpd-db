"""Snapshot-based key-level reconcile of contributor JSON work files.

Server adds keys to `gui2/data/{additions,corrections}_{user}.json`; the
maintainer's review processing removes keys upstream. A raw `git pull` would
conflict, so instead we reconcile per key against a snapshot of what was last
pushed:

    final = local - (last_pushed - main_version)

i.e. drop exactly the keys that were pushed and have since been removed
upstream (processed by the maintainer), while keeping everything the server
added locally since the last push.

REFINEMENT (Phase 1 dedup-by-id): keys are stable across re-edits of the same
word (`{username}_{id}`), so a key pushed and processed upstream can be edited
again locally under the same key. Such a fresh edit must NOT be dropped. A key
is dropped only when it is unchanged since the push (`local[key] ==
last_pushed[key]`); a changed entry is kept.
"""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

ContribDict = dict[str, dict]


def reconcile(
    local: ContribDict, pushed: ContribDict, upstream: ContribDict
) -> ContribDict:
    """Return the reconciled contributor dict.

    Drops a key only when it was pushed, has since been removed upstream, and is
    unchanged locally since that push. Everything else — locally-added keys,
    still-pending pushed keys, and locally re-edited keys — is kept.
    """
    result: ContribDict = {}
    for key, value in local.items():
        was_pushed = key in pushed
        removed_upstream = key not in upstream
        unchanged_since_push = was_pushed and value == pushed[key]
        if was_pushed and removed_upstream and unchanged_since_push:
            continue
        result[key] = value
    return result


def load_json_dict(path: Path) -> ContribDict:
    """Load a JSON dict from `path`. Missing file -> {}.

    Fails CLOSED on a CORRUPT file (invalid JSON / non-dict): raises rather than
    returning {}, so reconcile aborts instead of treating a momentarily-corrupt
    contributor file as empty and wiping its keys.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(
            f"expected a JSON object in {path}, got {type(data).__name__}"
        )
    return data


def write_json_dict(path: Path, data: ContribDict) -> None:
    """Atomically write a JSON dict, matching the gui2 managers' formatting.

    Writes to a temp file in the same dir then os.replace()s it, so a crash
    mid-write can never leave a half-written (corrupt) contributor file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=4) if data else "{}"
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def upstream_from_git(project_root: Path, ref: str, rel_path: str) -> ContribDict:
    """Return the JSON dict of `rel_path` at `ref`.

    A file absent at `ref` -> {} (normal: the maintainer emptied/removed it).
    Any OTHER git failure or invalid JSON raises (fails closed): silently
    returning {} would make reconcile treat every snapshot key as removed
    upstream and drop local data.
    """
    result = subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "does not exist" in stderr or "exists on disk, but not in" in stderr:
            return {}
        raise RuntimeError(
            f"git show {ref}:{rel_path} failed (rc={result.returncode}): "
            f"{result.stderr.strip()}"
        )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {ref}:{rel_path}: {exc}") from exc
    return data if isinstance(data, dict) else {}


def contributor_files(data_dir: Path) -> list[Path]:
    """Return the per-contributor work files (excluding the *_added review files)."""
    files: list[Path] = []
    for pattern in ("additions_*.json", "corrections_*.json"):
        for path in sorted(data_dir.glob(pattern)):
            if "_added" in path.name:
                continue
            files.append(path)
    return files


def reconcile_all(
    project_root: Path,
    data_dir: Path,
    snapshot_dir: Path,
    ref: str,
) -> dict[str, int]:
    """Reconcile every contributor file against its snapshot and upstream.

    Writes the reconciled result back to each file and refreshes its snapshot.
    Returns a map of filename -> remaining key count.
    """
    remaining: dict[str, int] = {}
    for local_path in contributor_files(data_dir):
        rel_path = local_path.relative_to(project_root).as_posix()
        upstream = upstream_from_git(project_root, ref, rel_path)
        snapshot_path = snapshot_dir / local_path.name
        pushed = load_json_dict(snapshot_path)
        local = load_json_dict(local_path)

        result = reconcile(local, pushed, upstream)
        write_json_dict(local_path, result)
        write_json_dict(snapshot_path, result)
        remaining[local_path.name] = len(result)
    return remaining


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Contributor data dir (default: <project-root>/gui2/data).",
    )
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=None,
        help="last_pushed snapshot dir (default: <data-dir>/last_pushed).",
    )
    parser.add_argument(
        "--ref",
        default="origin/main",
        help="Git ref holding the upstream (processed) version.",
    )
    args = parser.parse_args()

    project_root: Path = args.project_root
    data_dir: Path = args.data_dir or project_root / "gui2" / "data"
    snapshot_dir: Path = args.snapshot_dir or data_dir / "last_pushed"

    remaining = reconcile_all(project_root, data_dir, snapshot_dir, args.ref)
    for name, count in remaining.items():
        print(f"{name}: {count} keys remaining")


if __name__ == "__main__":
    main()
