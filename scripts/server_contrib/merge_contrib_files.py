"""Fold every contributor's own flag files into the shared files.

Run by the maintainer after merging the `contributions` branch, from the repo
root (`just contrib-merge` does the merge and this):

    uv run scripts/server_contrib/merge_contrib_files.py [data_dir]

`data_dir` is where the branch put the contributor files (default `gui2/data`).
The contributor files are left as they are.

Merged-lines log: `gui2/data/contrib_lines_merged.json` is
`{contributor_file_name: [line, ...]}`. A line in the log is never merged again,
so a line the maintainer later deletes or changes in a shared file does not come
back. Every handled line is logged: added, already present, or a test
exception for a test that no longer exists. A test exception whose id is at or
above CONTRIB_ID_BASE is a contributor's reserved id, means nothing on main,
and is reported but neither merged nor logged. The header line of a variant or
spelling file is neither merged nor logged. The server's reconcile drops the
logged lines.

Each shared file keeps the format and order its own writer gives it. Measured
on the real files:

user_dictionary.txt (`shared_data/`; writer `CustomSpellChecker.add_to_dictionary`
in `tools/spelling.py`)
    One word per line, LF, no duplicates, sorted by `(word.lower(), word)`.
    Merge: union the words and rewrite the whole file in that order.

checked.csv (`shared_data/deconstructor/`; writers `update_sandhi_checked` in
`gui2/mixins.py` and `add_sandhi_to_checked_csv` in `gui2/sandhi_files_manager.py`)
    No header, one sandhi word per line, in the order they were added (not
    sorted, a few CRLF lines in the middle, 197 repeated words).
    Merge: append each word not already a line, as a new LF line.

manual_corrections.tsv (same folder; writers `update_sandhi_corrections` and
`update_sandhi_corrections_csv`)
    Header `compound<TAB>split`, then `sandhi<TAB>breakup` per line, in the
    order they were added (not sorted, a few CRLF lines, 64 repeated keys).
    Merge: append each line not already present, as a new LF line. A new split
    for a known word is appended, not swapped, so the maintainer sees both.

variant_readings.tsv and spelling_mistakes.tsv (same folder; writers
`VariantReadingFileManager.update_and_save` and
`SpellingMistakesFileManager.update_and_save`)
    CRLF, header (`variant<TAB>main`, `mistake<TAB>correction`), then one pair
    per line in the order they were first added (not sorted), one line per key.
    Merge: a new key goes at the end, a known key with a new value changes in
    place (as `update_and_save` does), and the file is rewritten with the
    existing header.

db_tests_columns.tsv (`db_tests/`; writer `DbTestManager.save_tests`)
    One test per row; the `exceptions` column is a sorted JSON list of ids.
    A contributor's `db_test_exceptions_{user}.tsv` holds `test_name<TAB>id`.
    Merge: add each id to the named test and save through `DbTestManager`, so
    the file is written exactly as the Tests tab writes it. A line naming a test
    that no longer exists is reported and skipped.
"""

import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from db_tests.db_tests_manager import DbTestManager
from gui2.database_manager import CONTRIB_ID_BASE
from gui2.paths import Gui2Paths
from tools.contrib_entry import delivered_files
from tools.pali_sort_key import pali_sort_key
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv_2col_to_dict, write_tsv_2col_from_dict

Report = dict[str, list[str]]
MergedLog = dict[str, list[str]]


@dataclass(frozen=True)
class SharedFiles:
    user_dictionary: Path
    sandhi_checked: Path
    sandhi_corrections: Path
    variant_readings: Path
    spelling_mistakes: Path
    tests_columns: Path

    @staticmethod
    def default() -> "SharedFiles":
        paths = Gui2Paths()
        return SharedFiles(
            user_dictionary=paths.user_dictionary_path,
            sandhi_checked=paths.sandhi_checked_path,
            sandhi_corrections=paths.sandhi_corrections_path,
            variant_readings=paths.variant_readings_path,
            spelling_mistakes=paths.spelling_mistakes_path,
            tests_columns=DbTestManager().tests_path,
        )


def _lines(path: Path) -> list[str]:
    """The non-blank lines of a file, without line endings. [] if missing."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        # Split on "\n" only: str.splitlines() also splits on characters that
        # can sit inside a text line.
        return [line.rstrip("\r") for line in f.read().split("\n") if line.strip()]


def read_merged_log(path: Path) -> MergedLog:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def write_merged_log(path: Path, log: MergedLog) -> None:
    """Keys and lines in Pāḷi sort order, so a rerun never reorders the file."""
    ordered = {
        name: sorted(set(log[name]), key=pali_sort_key)
        for name in sorted(log, key=pali_sort_key)
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=4)


def merge_user_dictionary(lines: list[str], shared: Path) -> list[str]:
    existing = _lines(shared)
    known = set(existing)
    new = sorted({w.strip() for w in lines} - known)
    if not new:
        return []
    merged = sorted(known | set(new), key=lambda w: (w.lower(), w))
    with open(shared, "w", encoding="utf-8", newline="") as f:
        f.write("\n".join(merged) + "\n")
    return new


def merge_appended_lines(lines: list[str], shared: Path) -> list[str]:
    known = set(_lines(shared))
    new: list[str] = []
    for line in lines:
        if line not in known:
            known.add(line)
            new.append(line)
    if not new:
        return []
    with open(shared, encoding="utf-8", newline="") as f:
        ends_with_newline = f.read().endswith("\n")
    with open(shared, "a", encoding="utf-8", newline="") as f:
        if not ends_with_newline:
            f.write("\n")
        f.write("".join(f"{line}\n" for line in new))
    return new


def merge_two_column(lines: list[str], shared: Path) -> list[str]:
    own: dict[str, str] = {}
    for line in lines:
        key, _, value = line.partition("\t")
        own[key] = value
    shared_data, headers = read_tsv_2col_to_dict(shared)
    report: list[str] = []
    for key, value in own.items():
        if key not in shared_data:
            report.append(f"{key}\t{value}")
        elif shared_data[key] != value:
            report.append(f"{key}\t{value} (was {shared_data[key]})")
        else:
            continue
        shared_data[key] = value
    if report:
        write_tsv_2col_from_dict(shared, shared_data, headers or None)
    return report


def is_reserved_exception(line: str) -> bool:
    _, _, raw_id = line.partition("\t")
    return raw_id.strip().isdigit() and int(raw_id) >= CONTRIB_ID_BASE


def merge_test_exceptions(lines: list[str], tests_path: Path) -> list[str]:
    manager = DbTestManager()
    manager.tests_path = tests_path
    manager.internal_tests_list = manager.load_tests()
    by_name = {test.test_name: test for test in manager.internal_tests_list}
    report: list[str] = []
    changed = False
    for line in lines:
        test_name, _, raw_id = line.partition("\t")
        test = by_name.get(test_name)
        if is_reserved_exception(line):
            report.append(f"skipped (reserved id, means nothing on main): {line}")
            continue
        if test is None or not raw_id.strip().isdigit():
            report.append(f"skipped (no such test or bad id): {line}")
            continue
        exception_id = int(raw_id)
        if exception_id in test.exceptions:
            continue
        test.exceptions.append(exception_id)
        test.exceptions.sort()
        changed = True
        report.append(f"{test_name}\t{exception_id}")
    if changed:
        manager.save_tests()
    return report


def merge_all(
    data_dir: Path, shared: SharedFiles, log_path: Path | None = None
) -> Report:
    """Merge every contributor file in data_dir. Returns what was added, per
    contributor file name. With a log_path the merged-lines log is read first
    and written after; without one, nothing is remembered between calls."""
    log = read_merged_log(log_path) if log_path else {}
    found = delivered_files(data_dir)
    report: Report = {}
    jobs: tuple[tuple[str, Callable[[list[str], Path], list[str]], Path, bool], ...] = (
        ("user_dictionary", merge_user_dictionary, shared.user_dictionary, False),
        ("checked", merge_appended_lines, shared.sandhi_checked, False),
        ("manual_corrections", merge_appended_lines, shared.sandhi_corrections, False),
        ("variant_readings", merge_two_column, shared.variant_readings, True),
        ("spelling_mistakes", merge_two_column, shared.spelling_mistakes, True),
        ("db_test_exceptions", merge_test_exceptions, shared.tests_columns, False),
    )
    for kind, merge, shared_path, has_header in jobs:
        for contrib in found[kind]:
            lines = _lines(contrib)
            if has_header:
                lines = lines[1:]
            logged = set(log.get(contrib.name, []))
            fresh = [line for line in lines if line not in logged]
            report[contrib.name] = merge(fresh, shared_path)
            handled = [
                line
                for line in fresh
                if not (kind == "db_test_exceptions" and is_reserved_exception(line))
            ]
            log[contrib.name] = [*logged, *handled]
    if log_path and report:
        write_merged_log(log_path, log)
    return report


def main(argv: list[str]) -> int:
    data_dir = Path(argv[1]) if len(argv) > 1 else Path("gui2/data")
    log_path = Gui2Paths().contrib_lines_merged_path
    report = merge_all(data_dir, SharedFiles.default(), log_path)
    if not report:
        pr.red(f"no contributor files found in {data_dir}")
        return 1
    for name, added in report.items():
        pr.green_title(f"{name}: {len(added)} added")
        for item in added:
            pr.white(f"  {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
