"""Pull the contributors' files from the server to this laptop, once a day.

Started by the systemd user timer (`just contrib-pull-install`) or by hand
(`just contrib-pull`). The design is in
`kamma/threads/20261023_contrib_1_web_server/pull_spec.md`.

Every file is checked before it is used. The server is outside the laptop's
trust, so a file that fails a check is dropped, together with all the other
files of the same contributor.
"""

import argparse
import fcntl
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path

import psutil

from gui2.paths import Gui2Paths
from scripts.server_contrib.contrib_reconcile import (
    _read_lines,
    _write_atomic,
    is_reserved_exception,
    reconcile_all,
)
from scripts.server_contrib.merge_contrib_files import SharedFiles, merge_all
from tools.configger import config_read
from tools.contrib_entry import DELIVERED_KINDS

USER_PATTERN = re.compile(r"[a-z][a-z0-9_]{0,31}")
MAX_LINE_LENGTH = 500
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_LISTING = 200
# Relative to the folder `rrsync` serves; settled by task 5.3.
REMOTE_SOURCE_SUFFIX = ":"
KEY_PATH = Path.home() / ".ssh" / "dpd_contrib_pull"
NOTICE_FROM = time(22, 30)
EDITOR_OPEN = "skipped: editor open"
JSON_KINDS = ("additions", "corrections")
# The merge step drops line 1 of these files as the header, so a file without
# the header would lose its first pair without a word.
TWO_COLUMN_HEADERS = {
    "variant_readings": "variant\tmain",
    "spelling_mistakes": "mistake\tcorrection",
}
RSYNC_DEADLINE = 300
MAX_OUTCOME_LENGTH = 300
# One word per line. A tab would put a second column into a one-column file.
ONE_COLUMN_KINDS = ("user_dictionary", "checked")
# The merge appends these lines to a two-column file, and the Go reader indexes
# the header by column, so a line with 3 columns stops the whole build.
TWO_COLUMN_NO_HEADER_KINDS = ("manual_corrections",)
ID_TEXT = re.compile(r"[0-9]{1,12}")
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
EXCEPTION_LINE = re.compile(r"[^\t]+\t[0-9]+")
SSH_OPTIONS: list[str] = [
    "ssh",
    "-i",
    str(KEY_PATH),
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=accept-new",
    "-o",
    "IdentitiesOnly=yes",
    "-o",
    "ForwardAgent=no",
    "-o",
    "ConnectTimeout=30",
    "-o",
    "ControlPath=none",
    "-o",
    "ClearAllForwardings=yes",
]


class PullError(Exception):
    pass


def glob_parts(name: str) -> tuple[str, str] | None:
    """(kind, user part) of a name that matches a delivered pattern, with no
    check on the user part. The user part is what the pattern's `*` covers, cut
    out by the literal prefix and suffix, not found by a second regex."""
    for pattern, kind in DELIVERED_KINDS:
        if fnmatch.fnmatchcase(name, pattern):
            prefix, _, suffix = pattern.partition("*")
            return kind, name[len(prefix) : len(name) - len(suffix)]
    return None


def kind_of(name: str) -> str | None:
    """The kind of a file name the server may deliver, else None. Each kind has
    one extension, the user part is a plain lower-case word, and a name with
    `added` is a review log, not a contributor file."""
    parts = glob_parts(name)
    if parts is None or "added" in name:
        return None
    kind, user = parts
    return kind if USER_PATTERN.fullmatch(user) else None


def user_of(name: str) -> str:
    parts = glob_parts(name)
    if kind_of(name) is None or parts is None:
        raise ValueError(f"not a contributor file name: {name[:80]!r}")
    return parts[1]


def check_content(path: Path, kind: str) -> str | None:
    """Why this file must not be used, or None if it is fine."""
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return "not valid UTF-8"
    if kind in JSON_KINDS:
        return _check_json(text)
    return _check_lines(text, kind)


def _check_json(text: str) -> str | None:
    try:
        data = json.loads(text)
    except (ValueError, RecursionError):
        return "not valid JSON"
    if not isinstance(data, dict):
        return "JSON top level is not an object"
    if not all(isinstance(value, dict) for value in data.values()):
        return "a JSON entry is not an object"
    for entry in data.values():
        entry_id = entry.get("id", 0)
        if isinstance(entry_id, bool) or not (
            isinstance(entry_id, int)
            or (isinstance(entry_id, str) and ID_TEXT.fullmatch(entry_id))
        ):
            # The reconcile step turns an id into an int, and a huge or odd
            # digit string raises there and stops the run for everyone.
            return "an entry id is not a plain number"
    return None


def _check_lines(text: str, kind: str) -> str | None:
    if CONTROL_CHARACTERS.search(text):
        return "control character"
    if text and not text.endswith("\n"):
        return "no final newline"
    header = TWO_COLUMN_HEADERS.get(kind)
    first_line = True
    for line in text.split("\n"):
        line = line.removesuffix("\r")
        if len(line) > MAX_LINE_LENGTH:
            return f"line longer than {MAX_LINE_LENGTH} characters"
        if not line.strip():
            continue
        if header is not None:
            if first_line and line != header:
                return "first line is not the header"
            fields = line.split("\t")
            if len(fields) != 2 or not all(fields):
                return "line without exactly 2 filled columns"
        first_line = False
        if kind in ONE_COLUMN_KINDS and "\t" in line:
            return "line has a tab in a one-column file"
        if kind in TWO_COLUMN_NO_HEADER_KINDS:
            fields = line.split("\t")
            if len(fields) != 2 or not all(fields):
                return "line without exactly 2 filled columns"
        if kind == "db_test_exceptions" and not EXCEPTION_LINE.fullmatch(line):
            return "line is not <test name><TAB><id>"
    return None


def _rsync(args: list[str], ssh: list[str]) -> str:
    """Run rsync, with the ssh options when the source is remote (`ssh` is
    empty for a local folder). Raises PullError with rsync's own message."""
    command = ["rsync", *args]
    if ssh:
        command[1:1] = ["-e", shlex.join(ssh)]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=RSYNC_DEADLINE
        )
    except subprocess.TimeoutExpired:
        raise PullError(f"rsync gave no answer in {RSYNC_DEADLINE} s") from None
    if result.returncode != 0:
        raise PullError(f"rsync failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout


def list_source(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]:
    """(name, size, is_regular_file) for everything in the source folder, with
    nothing copied, one level deep (a sub-folder shows as a `d` entry, so a
    hostile tree is never walked). A line is `mode size date time name`; the size has comma
    separators and a regular file has a mode that starts with `-` (a link
    starts with `l`, a folder with `d`)."""
    listing: list[tuple[str, int, bool]] = []
    for line in _rsync(["--list-only", "--timeout=60", source], ssh).splitlines():
        parts = line.split(None, 4)
        if len(parts) != 5 or parts[4] == ".":
            continue
        mode, size, _date, _time, name = parts
        listing.append((name, int(size.replace(",", "")), mode.startswith("-")))
    return listing


def copy_names(source: str, names: list[str], scratch: Path, ssh: list[str]) -> None:
    """Copy exactly these names into scratch. No `-a`: no links, no permission
    or owner copy, and a 60 s timeout."""
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".txt"
    ) as names_file:
        names_file.write("".join(f"{name}\n" for name in names))
        names_file.flush()
        _rsync(
            [
                f"--files-from={names_file.name}",
                "--no-links",
                "--no-perms",
                "--no-owner",
                "--no-group",
                "--timeout=60",
                f"--max-size={MAX_FILE_BYTES}",
                source,
                f"{scratch}/",
            ],
            ssh,
        )


def select_names(
    listing: list[tuple[str, int, bool]],
) -> tuple[list[str], dict[str, str]]:
    """The names to copy, and `user -> reason` for every contributor with a bad
    name. A bad name drops all of that contributor's names. A name with no
    readable user is never copied and never blamed on anyone (see
    `ignored_names`)."""
    if len(listing) > MAX_LISTING:
        raise PullError("too many files")
    bad: dict[str, str] = {}
    good: list[tuple[str, str]] = []
    for name, size, regular in listing:
        parts = glob_parts(name)
        if parts is None or not USER_PATTERN.fullmatch(parts[1]):
            continue
        user = parts[1]
        if not regular:
            bad.setdefault(user, f"{name} is not a regular file")
        elif size > MAX_FILE_BYTES:
            bad.setdefault(user, f"{name} is over 5 MB")
        elif kind_of(name) is None:
            bad.setdefault(user, f"{name} is not an allowed name")
        else:
            good.append((name, user))
    return [name for name, user in good if user not in bad], bad


def ignored_names(listing: list[tuple[str, int, bool]]) -> list[str]:
    """Names that match a delivered pattern but have no readable user part."""
    ignored: list[str] = []
    for name, _size, _regular in listing:
        parts = glob_parts(name)
        if parts is not None and not USER_PATTERN.fullmatch(parts[1]):
            ignored.append(name)
    return ignored


def check_scratch(scratch: Path, bad: dict[str, str]) -> dict[str, str]:
    """Add `user -> reason` for the first file of each contributor that fails
    its content check. Returns a new map."""
    result = dict(bad)
    for path in sorted(scratch.iterdir()):
        kind = kind_of(path.name)
        if kind is None:
            continue
        user = user_of(path.name)
        if user in result:
            continue
        reason = check_content(path, kind)
        if reason:
            result[user] = f"{path.name}: {reason}"
    return result


def remove_users(scratch: Path, bad: dict[str, str]) -> None:
    """Delete every scratch file of a contributor named in `bad`, and any file
    whose name is not a contributor file."""
    for path in scratch.iterdir():
        if kind_of(path.name) is None or user_of(path.name) in bad:
            path.unlink()


def drop_foreign_exceptions(scratch: Path) -> int:
    """Drop every test-exception line whose id is not a reserved id. A
    contributor can only hold exceptions for their own new words; the merge
    step would add any other id to a real test. Returns the lines dropped."""
    dropped = 0
    for path in scratch.glob("db_test_exceptions_*.tsv"):
        lines = _read_lines(path)
        kept = [line for line in lines if is_reserved_exception(line)]
        dropped += sum(1 for line in lines if line.strip()) - len(kept)
        if kept != lines:
            _write_atomic(path, "".join(kept))
    return dropped


def prepare(
    scratch: Path, repo: Path, bad: dict[str, str]
) -> tuple[dict[str, str], int]:
    """Check, drop bad contributors, drop what the maintainer already handled,
    drop foreign exception ids. Returns `(bad, dropped_exception_lines)`."""
    bad = check_scratch(scratch, bad)
    remove_users(scratch, bad)
    reconcile_all(repo, scratch)
    return bad, drop_foreign_exceptions(scratch)


def editor_running() -> bool:
    """True if another process has an argument that ends in `gui2/main.py`.
    Matched on single arguments, never on the whole command line, so a command
    that only mentions the path does not count."""
    me = os.getpid()
    for process in psutil.process_iter(["pid", "cmdline"]):
        if process.info["pid"] == me:
            continue
        if any(arg.endswith("gui2/main.py") for arg in process.info["cmdline"] or []):
            return True
    return False


def copy_in(scratch: Path, data_dir: Path) -> list[str]:
    """Copy every scratch file into data_dir, one atomic rename per file."""
    copied: list[str] = []
    for path in sorted(scratch.iterdir()):
        target = data_dir / path.name
        temp = data_dir / f"{path.name}.tmp"
        try:
            shutil.copyfile(path, temp)
            os.replace(temp, target)
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
        copied.append(path.name)
    return copied


@dataclass
class Status:
    outcome: str = ""
    finished: str = ""
    last_success: str | None = None
    contributors: list[str] = field(default_factory=list)
    lines_added: int = 0
    test_lines_dropped: int = 0
    ignored_names: int = 0
    notice_error: str | None = None

    def text(self) -> str:
        lines = [f"outcome: {self.outcome}", f"finished: {self.finished}"]
        if self.last_success:
            lines.append(f"last_success: {self.last_success}")
        lines += self.contributors
        lines += [
            f"lines_added: {self.lines_added}",
            f"test_lines_dropped: {self.test_lines_dropped}",
            f"ignored_names: {self.ignored_names}",
        ]
        if self.notice_error:
            lines.append(f"notice_error: {self.notice_error}")
        return "\n".join(lines) + "\n"


def read_status(path: Path) -> Status:
    """The earlier run's status. A missing or unreadable file gives a Status
    with no `last_success`. Only the first `last_success:` line counts, because
    a contributor line comes after it and could carry any user name."""
    status = Status()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return status
    for line in text.split("\n"):
        if line.startswith("last_success: "):
            try:
                status.last_success = date.fromisoformat(line[14:].strip()).isoformat()
            except ValueError:
                pass
            break
    return status


def write_status(path: Path, status: Status) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomic(path, status.text())


def _is_remote(source: str) -> bool:
    """rsync's own rule: a `host:` before any slash is a remote source."""
    return re.match(r"[^/]+:", source) is not None


def redact(text: str, source: str) -> str:
    """Remove the ssh target and the key path from a message, so neither is
    ever written to the status file or the log."""
    secrets = [str(KEY_PATH)]
    if _is_remote(source):
        target = source.partition(":")[0]
        secrets += [source, target, target.rpartition("@")[2]]
    for secret in sorted(set(filter(None, secrets)), key=len, reverse=True):
        text = text.replace(secret, "<hidden>")
    return text


def _log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{line}\n")


def _summarise(scratch: Path, bad: dict[str, str], verb: str) -> list[str]:
    """One status line per contributor: files and entries, or why skipped."""
    files: dict[str, list[Path]] = {}
    for path in scratch.iterdir():
        files.setdefault(user_of(path.name), []).append(path)
    lines: dict[str, str] = {
        user: f"{user}: skipped, {why}" for user, why in bad.items()
    }
    for user, paths in files.items():
        entries = sum(
            len(json.loads(path.read_text(encoding="utf-8")))
            for path in paths
            if kind_of(path.name) in JSON_KINDS
        )
        lines[user] = f"{user}: {verb} {len(paths)} files, {entries} entries"
    return [lines[user] for user in sorted(lines)]


def _pull(
    source: str,
    repo: Path,
    shared: SharedFiles,
    status: Status,
    log_path: Path,
    now: datetime,
    dry_run: bool,
    scratch: Path,
) -> None:
    """Steps 2 to 7 of the spec. Sets `status.outcome`; any exception is for
    `run` to turn into `failed`."""
    ssh = SSH_OPTIONS if _is_remote(source) else []
    listing = list_source(source, ssh)
    names, bad = select_names(listing)
    ignored = ignored_names(listing)
    status.ignored_names = len(ignored)
    for name in ignored:
        if not dry_run:
            _log(log_path, f"ignored name: {redact(name[:80], source)!r}")
    if names:
        copy_names(source, names, scratch, ssh)
    bad, status.test_lines_dropped = prepare(scratch, repo, bad)
    status.contributors = _summarise(
        scratch, bad, "would copy" if dry_run else "pulled"
    )
    if dry_run:
        status.outcome = "dry run, nothing copied"
        return
    if editor_running():
        status.outcome = EDITOR_OPEN
        return
    data_dir = Gui2Paths(repo).gui2_data_path
    copy_in(scratch, data_dir)
    if editor_running():
        status.outcome = "partial"
        return
    report = merge_all(data_dir, shared, Gui2Paths(repo).contrib_lines_merged_path)
    status.lines_added = sum(
        1
        for items in report.values()
        for item in items
        if not item.startswith("skipped")
    )
    if bad:
        status.outcome = "pulled with problems"
    elif status.contributors:
        status.outcome = "pulled"
    else:
        status.outcome = "pulled, no contributor files"
    status.last_success = now.date().isoformat()


def run(
    source: str,
    repo: Path,
    shared: SharedFiles,
    status_path: Path,
    lock_path: Path,
    now: datetime,
    dry_run: bool,
) -> Status:
    """One pull. A skipped run returns its reason and writes nothing, so the
    status file keeps the last real result. A dry run writes nothing either."""
    previous = read_status(status_path)
    status = Status(
        finished=now.strftime("%Y-%m-%d %H:%M"), last_success=previous.last_success
    )
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            status.outcome = "skipped: another run"
            return status
        if not dry_run:
            if previous.last_success == now.date().isoformat():
                status.outcome = "skipped: already done today"
                return status
            if editor_running():
                status.outcome = EDITOR_OPEN
                return status
        log_path = status_path.with_name("contrib_pull.log")
        try:
            with tempfile.TemporaryDirectory(prefix="contrib_pull_") as scratch:
                _pull(
                    source, repo, shared, status, log_path, now, dry_run, Path(scratch)
                )
        except (
            PullError,
            RuntimeError,
            OSError,
            ValueError,
            subprocess.SubprocessError,
        ) as exc:
            reason = " ".join(redact(str(exc), source).split())
            status.outcome = f"failed: {reason[:MAX_OUTCOME_LENGTH]}"
    if dry_run or status.outcome.startswith("skipped"):
        return status
    write_status(status_path, status)
    _log(log_path, f"{status.finished} {status.outcome}")
    return status


def notify(message: str) -> None:
    subprocess.run(
        ["notify-send", "DPD contributor pull", message],
        check=True,
        capture_output=True,
        timeout=10,
    )


def maybe_notify(status: Status, now: datetime) -> None:
    """Tell the maintainer about a run that went wrong. A run that skipped a
    contributor counts as the day's success, so no later run would report it:
    it is announced at once. A failed or partial run is announced on the last
    run of the day only, because the next run may repair it. A failed notice is
    noted in the status, never raised."""
    problems = status.outcome.startswith("pulled with problems")
    broken = status.outcome.startswith(("failed", "partial"))
    if not (problems or (broken and now.time() >= NOTICE_FROM)):
        return
    try:
        notify(status.outcome)
    except (OSError, subprocess.SubprocessError) as exc:
        status.notice_error = str(exc)[:200]


def notify_editor_open(status: Status) -> None:
    """Tell the maintainer the pull skipped because gui2 is open. A skip writes
    no status file, so the notice is the only sign of it. A failed notice is
    ignored: the next run tries again."""
    try:
        notify(status.outcome)
    except (OSError, subprocess.SubprocessError):
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    target = config_read("epitaka_server", "ssh")
    if not target:
        sys.stderr.write("[epitaka_server] ssh is not set in config.ini\n")
        return 1
    repo = Path.cwd()
    logs = repo / "logs"
    now = datetime.now()
    status_path = logs / "contrib_pull_status.txt"
    status = run(
        f"{target}{REMOTE_SOURCE_SUFFIX}",
        repo,
        SharedFiles.default(),
        status_path,
        logs / "contrib_pull.lock",
        now,
        args.dry_run,
    )
    if not args.dry_run:
        if status.outcome == EDITOR_OPEN:
            notify_editor_open(status)
        elif not status.outcome.startswith("skipped"):
            maybe_notify(status, now)
            if status.notice_error:
                write_status(status_path, status)
    sys.stdout.write(status.text())
    return 0 if status.outcome.startswith(("pulled", "skipped", "dry run")) else 1


if __name__ == "__main__":
    sys.exit(main())
