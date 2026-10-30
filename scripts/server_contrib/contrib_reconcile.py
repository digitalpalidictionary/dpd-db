"""Drop from the server's contributor files what main has already handled.

Run in the nightly window right after `git pull`, so the working tree is main.

JSON entries (`additions_*.json`, `corrections_*.json`): the maintainer logs
every accepted or rejected entry in main's `additions_added.json` /
`corrections_added.json` as `(_source_key, _source_hash)`. A local entry is
dropped when its `(key, entry_hash)` is in that log. An entry the contributor
edited again after review has a new hash, so it stays.

Flag lines (user dictionary, checked, manual corrections, variants, spelling,
test exceptions): `merge_contrib_files.py` logs every line it handles in
`contrib_lines_merged.json`. A local line is dropped when it is logged for that
file. The header line of a variant or spelling file always stays: it equals the
shared header, and the reader takes line 1 as the header, so dropping it would
turn the first pair into a header.

A test exception on a reserved id (CONTRIB_ID_BASE and up) means nothing on
main, so it is dropped once the contributor's additions no longer hold that id.
`get_next_id` gives the same id to the next new word after processing.

An emptied file is written back, never deleted.
"""

import argparse
import json
import os
import tempfile
from pathlib import Path

from gui2.database_manager import CONTRIB_ID_BASE
from gui2.paths import Gui2Paths
from tools.contrib_entry import delivered_files, entry_hash

ContribDict = dict[str, dict]
Processed = set[tuple[str, str]]

# Kinds whose first line is a header that must stay.
HEADER_KINDS = ("variant_readings", "spelling_mistakes")
LINE_KINDS = (
    "user_dictionary",
    "checked",
    "manual_corrections",
    "variant_readings",
    "spelling_mistakes",
)


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


def _write_atomic(path: Path, content: str) -> None:
    """Write to a temp file in the same dir then os.replace() it, so a crash
    mid-write can never leave a half-written contributor file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def write_json_dict(path: Path, data: ContribDict) -> None:
    """Atomically write a JSON dict, matching the gui2 managers' formatting."""
    content = json.dumps(data, ensure_ascii=False, indent=4) if data else "{}"
    _write_atomic(path, content)


def load_processed(log_path: Path) -> Processed:
    """The `(_source_key, _source_hash)` pairs in one processed log. Missing
    file -> empty. A corrupt log raises, so nothing is dropped on a guess."""
    try:
        with open(log_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return set()
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON in {log_path}: {exc}") from exc
    if not isinstance(data, list):
        raise RuntimeError(f"expected a JSON list in {log_path}")
    return {
        (row["_source_key"], row["_source_hash"])
        for row in data
        if isinstance(row, dict) and "_source_key" in row and "_source_hash" in row
    }


def load_merged_lines(log_path: Path) -> dict[str, set[str]]:
    """The merged-lines log: contributor file name -> logged lines."""
    data = load_json_dict(log_path)
    return {name: set(lines) for name, lines in data.items()}


def reconcile_entries(local: ContribDict, processed: Processed) -> ContribDict:
    """Drop every entry whose (key, hash) main has processed."""
    return {
        key: value
        for key, value in local.items()
        if (key, entry_hash(value)) not in processed
    }


def reconcile_lines(
    local_lines: list[str], merged_lines: set[str], keep_header: bool
) -> list[str]:
    """Drop the lines the maintainer has merged. Each line keeps its own ending."""
    kept: list[str] = []
    for index, line in enumerate(local_lines):
        if keep_header and index == 0:
            kept.append(line)
        elif line.rstrip("\r\n") not in merged_lines:
            kept.append(line)
    return kept


def is_reserved_exception(line: str) -> bool:
    _, _, raw_id = line.rstrip("\r\n").partition("\t")
    return raw_id.strip().isdigit() and int(raw_id) >= CONTRIB_ID_BASE


def reconcile_exception_lines(
    local_lines: list[str], merged_lines: set[str], held_ids: set[int]
) -> list[str]:
    """Drop merged exception lines, and reserved-id lines whose id no addition
    holds any more."""
    kept: list[str] = []
    for line in reconcile_lines(local_lines, merged_lines, keep_header=False):
        if is_reserved_exception(line):
            _, _, raw_id = line.rstrip("\r\n").partition("\t")
            if int(raw_id) not in held_ids:
                continue
        kept.append(line)
    return kept


def _read_lines(path: Path) -> list[str]:
    """Lines with their endings. Split on "\\n" only: str.splitlines() also
    splits on characters that can sit inside a text line."""
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    parts = text.split("\n")
    lines = [f"{part}\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def _held_ids(additions: ContribDict) -> set[int]:
    ids: set[int] = set()
    for entry in additions.values():
        raw = str(entry.get("id", ""))
        if raw.isdigit():
            ids.add(int(raw))
    return ids


def reconcile_all(project_root: Path, data_dir: Path) -> dict[str, int]:
    """Reconcile every delivered contributor file against main's logs.

    main's logs are read from `project_root` (the server is on main after the
    pull). Returns a map of file name -> remaining entry or line count.
    """
    main_paths = Gui2Paths(project_root)
    processed = load_processed(main_paths.additions_added_path) | load_processed(
        main_paths.corrections_added_path
    )
    merged = load_merged_lines(main_paths.contrib_lines_merged_path)
    found = delivered_files(data_dir)
    remaining: dict[str, int] = {}

    held_by_contributor: dict[str, set[int]] = {}
    for kind in ("additions", "corrections"):
        for path in found[kind]:
            local = load_json_dict(path)
            result = reconcile_entries(local, processed)
            if result != local:
                write_json_dict(path, result)
            remaining[path.name] = len(result)
            if kind == "additions":
                held_by_contributor[path.stem.removeprefix("additions_")] = _held_ids(
                    result
                )

    for kind in LINE_KINDS:
        for path in found[kind]:
            lines = _read_lines(path)
            kept = reconcile_lines(
                lines, merged.get(path.name, set()), kind in HEADER_KINDS
            )
            if kept != lines:
                _write_atomic(path, "".join(kept))
            remaining[path.name] = len(kept)

    for path in found["db_test_exceptions"]:
        lines = _read_lines(path)
        kept = reconcile_exception_lines(
            lines,
            merged.get(path.name, set()),
            held_by_contributor.get(
                path.stem.removeprefix("db_test_exceptions_"), set()
            ),
        )
        if kept != lines:
            _write_atomic(path, "".join(kept))
        remaining[path.name] = len(kept)
    return remaining


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Repository root, on main (default: current directory).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Contributor data dir (default: <project-root>/gui2/data).",
    )
    args = parser.parse_args()

    project_root: Path = args.project_root
    data_dir: Path = args.data_dir or project_root / "gui2" / "data"

    for name, count in reconcile_all(project_root, data_dir).items():
        print(f"{name}: {count} remaining")


if __name__ == "__main__":
    main()
