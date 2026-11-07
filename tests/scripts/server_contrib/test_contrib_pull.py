"""contrib_pull: name and content checks on files copied from the server."""

import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, time
from pathlib import Path

import pytest

from scripts.server_contrib import contrib_pull
from scripts.server_contrib.merge_contrib_files import SharedFiles
from tools.paths import ProjectPaths

from scripts.server_contrib.contrib_pull import (
    SSH_OPTIONS,
    PullError,
    Status,
    check_content,
    copy_names,
    drop_foreign_exceptions,
    editor_running,
    ignored_names,
    kind_of,
    list_source,
    maybe_notify,
    prepare,
    read_status,
    redact,
    run,
    select_names,
    user_of,
    write_status,
)
from tools.contrib_entry import entry_hash

ENTRY = {
    "id": 10000002,
    "lemma_1": "saṅkhasavhaya",
    "pos": "adj",
    "meaning_2": "called Saṅkha; named Saṅkha",
    "construction": "saṅkha + savhaya",
}

GOOD_CONTENT: dict[str, bytes] = {
    "additions": json.dumps({"alice_10000002": ENTRY}, ensure_ascii=False).encode(),
    "corrections": json.dumps({"alice_1": ENTRY}, ensure_ascii=False).encode(),
    "user_dictionary": "saṅkha\nupāgato\n".encode(),
    "checked": "dasahupāgato\n".encode(),
    "manual_corrections": "dasahupāgato\tdasahi + upāgato\n".encode(),
    "variant_readings": "variant\tmain\r\nabc\tabd\r\n".encode(),
    "spelling_mistakes": "mistake\tcorrection\r\nabc\tabd\r\n".encode(),
    "db_test_exceptions": b"construction: needs na\t10000005\n",
}

GOOD_NAMES: dict[str, str] = {
    "additions": "additions_alice.json",
    "corrections": "corrections_alice.json",
    "user_dictionary": "user_dictionary_alice.txt",
    "checked": "checked_alice.csv",
    "manual_corrections": "manual_corrections_alice.tsv",
    "variant_readings": "variant_readings_alice.tsv",
    "spelling_mistakes": "spelling_mistakes_alice.tsv",
    "db_test_exceptions": "db_test_exceptions_alice.tsv",
}


def write(tmp_path: Path, kind: str, content: bytes) -> Path:
    path = tmp_path / GOOD_NAMES[kind]
    path.write_bytes(content)
    return path


@pytest.mark.parametrize("kind", GOOD_NAMES)
def test_every_kind_has_a_good_name(kind: str) -> None:
    assert kind_of(GOOD_NAMES[kind]) == kind
    assert user_of(GOOD_NAMES[kind]) == "alice"


def test_a_user_name_may_hold_underscores_and_digits() -> None:
    assert user_of("additions_ravi_2.json") == "ravi_2"


def test_the_wrong_extension_for_a_kind_is_refused() -> None:
    assert kind_of("checked_alice.json") is None


def test_a_name_with_added_is_refused() -> None:
    assert kind_of("additions_added.json") is None
    assert kind_of("additions_alice_added.json") is None


@pytest.mark.parametrize(
    "user", ["Alice", "1alice", "a" * 33, "al ice", "al-ice", "../x", ""]
)
def test_a_bad_user_part_is_refused(user: str) -> None:
    assert kind_of(f"additions_{user}.json") is None


def test_a_user_part_of_32_characters_is_allowed() -> None:
    assert kind_of(f"additions_{'a' * 32}.json") == "additions"


def test_a_name_in_a_sub_folder_is_refused() -> None:
    assert kind_of("sub/additions_alice.json") is None


def test_files_the_server_never_delivers_are_refused() -> None:
    assert kind_of("history_alice.json") is None
    assert kind_of("daily_log_alice.json") is None


@pytest.mark.parametrize("kind", GOOD_NAMES)
def test_a_good_file_of_each_kind_passes(tmp_path: Path, kind: str) -> None:
    assert check_content(write(tmp_path, kind, GOOD_CONTENT[kind]), kind) is None


@pytest.mark.parametrize("kind", ["additions", "corrections"])
def test_invalid_json_is_refused(tmp_path: Path, kind: str) -> None:
    assert check_content(write(tmp_path, kind, b'{"a": '), kind) is not None


def test_a_json_list_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "additions", b"[1, 2]"), "additions")


def test_a_json_value_that_is_not_a_dict_is_refused(tmp_path: Path) -> None:
    content = b'{"alice_1": {"id": 1}, "alice_2": "text"}'
    assert check_content(write(tmp_path, "additions", content), "additions")


def test_json_nested_100000_deep_is_refused_not_crashed(tmp_path: Path) -> None:
    content = b"[" * 100_000
    assert check_content(write(tmp_path, "additions", content), "additions")


def test_json_that_is_not_utf8_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "additions", b'{"a": "\xff"}'), "additions")


def test_a_flag_file_with_no_final_newline_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "checked", b"abc"), "checked")


def test_a_flag_line_of_501_characters_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "checked", b"a" * 501 + b"\n"), "checked")


def test_a_flag_line_of_500_characters_passes(tmp_path: Path) -> None:
    assert (
        check_content(write(tmp_path, "checked", b"a" * 500 + b"\n"), "checked") is None
    )


def test_a_nul_byte_in_a_flag_file_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "checked", b"ab\x00c\n"), "checked")


def test_a_flag_file_that_is_not_utf8_is_refused(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "checked", b"\xff\xfe\n"), "checked")


def test_an_empty_flag_file_passes(tmp_path: Path) -> None:
    assert check_content(write(tmp_path, "checked", b""), "checked") is None


@pytest.mark.parametrize("kind", ["variant_readings", "spelling_mistakes"])
def test_a_two_column_file_with_three_columns_is_refused(
    tmp_path: Path, kind: str
) -> None:
    assert check_content(write(tmp_path, kind, b"a\tb\tc\n"), kind)


@pytest.mark.parametrize("kind", ["variant_readings", "spelling_mistakes"])
def test_a_two_column_file_with_one_column_is_refused(
    tmp_path: Path, kind: str
) -> None:
    assert check_content(write(tmp_path, kind, b"a\n"), kind)


@pytest.mark.parametrize("line", [b"no tab here\n", b"name\tabc\n", b"name\t12\t13\n"])
def test_a_bad_exception_line_is_refused(tmp_path: Path, line: bytes) -> None:
    assert check_content(
        write(tmp_path, "db_test_exceptions", line), "db_test_exceptions"
    )


@pytest.fixture
def server_folder(tmp_path: Path) -> Path:
    """A stand-in for the server folder, with the hostile cases in it."""
    folder = tmp_path / "server"
    (folder / "sub").mkdir(parents=True)
    for name in ("additions_alice.json", "checked_alice.csv", "history_alice.json"):
        (folder / name).write_bytes(GOOD_CONTENT["additions"])
    (folder / "additions_bob.json").write_bytes(b"x" * (5 * 1024 * 1024 + 1))
    (folder / "evil name.json").write_bytes(b"{}")
    (folder / "sub" / "additions_carol.json").write_bytes(b"{}")
    (folder / "additions_link.json").symlink_to("/etc/hostname")
    return folder


def test_listing_reports_names_sizes_and_file_types(server_folder: Path) -> None:
    listing = {
        name: (size, regular)
        for name, size, regular in list_source(f"{server_folder}/", [])
    }
    assert listing["additions_alice.json"] == (len(GOOD_CONTENT["additions"]), True)
    assert listing["additions_bob.json"] == (5 * 1024 * 1024 + 1, True)
    assert listing["evil name.json"][1] is True
    assert listing["additions_link.json"][1] is False
    assert listing["sub"][1] is False
    # Only one level is listed, so a hostile tree is never walked.
    assert "sub/additions_carol.json" not in listing
    assert "." not in listing


def test_copy_names_copies_only_the_names_given(
    server_folder: Path, tmp_path: Path
) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    copy_names(f"{server_folder}/", ["additions_alice.json"], scratch, [])
    assert [path.name for path in scratch.iterdir()] == ["additions_alice.json"]


def test_copy_names_never_lands_a_symlink(server_folder: Path, tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    copy_names(
        f"{server_folder}/",
        ["additions_alice.json", "additions_link.json"],
        scratch,
        [],
    )
    assert [path.name for path in scratch.iterdir()] == ["additions_alice.json"]


def test_a_source_that_does_not_exist_raises(tmp_path: Path) -> None:
    with pytest.raises(PullError):
        list_source(f"{tmp_path / 'nothing'}/", [])


def test_ssh_options_hold_the_fixed_safe_set() -> None:
    joined = " ".join(SSH_OPTIONS)
    for option in (
        "BatchMode=yes",
        "StrictHostKeyChecking=accept-new",
        "IdentitiesOnly=yes",
        "ForwardAgent=no",
        "ControlPath=none",
        "ClearAllForwardings=yes",
    ):
        assert option in joined
    assert SSH_OPTIONS[SSH_OPTIONS.index("-i") + 1] == str(
        Path.home() / ".ssh" / "dpd_contrib_pull"
    )


def listing_of(folder: Path) -> list[tuple[str, int, bool]]:
    return list_source(f"{folder}/", [])


def test_select_names_copies_only_good_names_and_names_bad_users(
    server_folder: Path,
) -> None:
    names, bad = select_names(listing_of(server_folder))
    assert sorted(names) == ["additions_alice.json", "checked_alice.csv"]
    assert set(bad) == {"bob", "link"}
    assert "5 MB" in bad["bob"]
    assert "regular" in bad["link"]


def test_a_symlink_is_never_selected(server_folder: Path) -> None:
    names, _ = select_names(listing_of(server_folder))
    assert "additions_link.json" not in names


def test_names_with_no_readable_user_are_ignored_and_counted(tmp_path: Path) -> None:
    (tmp_path / "additions_Alice.json").write_bytes(b"{}")
    (tmp_path / "additions_alice.json").write_bytes(b"{}")
    (tmp_path / "history_alice.json").write_bytes(b"{}")
    listing = listing_of(tmp_path)
    names, bad = select_names(listing)
    assert names == ["additions_alice.json"]
    assert bad == {}
    assert ignored_names(listing) == ["additions_Alice.json"]


def test_201_names_raise(tmp_path: Path) -> None:
    for number in range(201):
        (tmp_path / f"additions_u{number}.json").write_bytes(b"{}")
    with pytest.raises(PullError, match="too many files"):
        select_names(listing_of(tmp_path))


def test_200_names_are_allowed(tmp_path: Path) -> None:
    for number in range(200):
        (tmp_path / f"additions_u{number}.json").write_bytes(b"{}")
    names, bad = select_names(listing_of(tmp_path))
    assert len(names) == 200
    assert bad == {}


def make_repo(tmp_path: Path, processed: list[dict[str, str]]) -> Path:
    repo = tmp_path / "repo"
    data = repo / "gui2" / "data"
    data.mkdir(parents=True)
    (data / "additions_added.json").write_text(json.dumps(processed))
    return repo


def make_scratch(tmp_path: Path) -> Path:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    return scratch


def test_a_processed_word_is_dropped_and_a_new_one_stays(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path, [{"_source_key": "alice_1", "_source_hash": entry_hash(ENTRY)}]
    )
    scratch = make_scratch(tmp_path)
    other = {**ENTRY, "lemma_1": "other"}
    (scratch / "additions_alice.json").write_text(
        json.dumps({"alice_1": ENTRY, "alice_2": other})
    )
    prepare(scratch, repo, {})
    assert list(json.loads((scratch / "additions_alice.json").read_text())) == [
        "alice_2"
    ]


def test_a_word_edited_after_review_stays(tmp_path: Path) -> None:
    repo = make_repo(
        tmp_path, [{"_source_key": "alice_1", "_source_hash": entry_hash(ENTRY)}]
    )
    scratch = make_scratch(tmp_path)
    edited = {**ENTRY, "meaning_2": "changed after review"}
    (scratch / "additions_alice.json").write_text(json.dumps({"alice_1": edited}))
    prepare(scratch, repo, {})
    assert list(json.loads((scratch / "additions_alice.json").read_text())) == [
        "alice_1"
    ]


def test_one_bad_file_removes_all_of_that_contributors_files_only(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path, [])
    scratch = make_scratch(tmp_path)
    (scratch / "additions_alice.json").write_text("{broken")
    (scratch / "checked_alice.csv").write_bytes(GOOD_CONTENT["checked"])
    (scratch / "additions_bob.json").write_bytes(GOOD_CONTENT["additions"])
    (scratch / "checked_bob.csv").write_bytes(GOOD_CONTENT["checked"])
    bad, _ = prepare(scratch, repo, {})
    assert set(bad) == {"alice"}
    assert sorted(path.name for path in scratch.iterdir()) == [
        "additions_bob.json",
        "checked_bob.csv",
    ]


def test_a_non_reserved_exception_is_dropped_and_counted(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, [])
    scratch = make_scratch(tmp_path)
    reserved = {**ENTRY, "id": 10000005}
    (scratch / "additions_alice.json").write_text(json.dumps({"alice_5": reserved}))
    (scratch / "db_test_exceptions_alice.tsv").write_text(
        "construction: needs na\t123\nconstruction: needs na\t10000005\n"
    )
    _, dropped = prepare(scratch, repo, {})
    assert dropped == 1
    assert (scratch / "db_test_exceptions_alice.tsv").read_text() == (
        "construction: needs na\t10000005\n"
    )


def test_a_reserved_exception_no_word_holds_is_dropped_by_the_reconcile_step(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path, [])
    scratch = make_scratch(tmp_path)
    (scratch / "additions_alice.json").write_text("{}")
    (scratch / "db_test_exceptions_alice.tsv").write_text(
        "construction: needs na\t10000005\n"
    )
    prepare(scratch, repo, {})
    assert (scratch / "db_test_exceptions_alice.tsv").read_text() == ""


def test_drop_foreign_exceptions_keeps_crlf_endings(tmp_path: Path) -> None:
    path = tmp_path / "db_test_exceptions_alice.tsv"
    path.write_bytes(b"a test\t5\r\na test\t10000007\r\n")
    assert drop_foreign_exceptions(tmp_path) == 1
    assert path.read_bytes() == b"a test\t10000007\r\n"


DECON = Path("shared_data/deconstructor")
DAY_ONE = datetime(2026, 11, 4, 9, 0)
DAY_TWO = datetime(2026, 11, 5, 9, 0)


@pytest.fixture
def shared(tmp_path: Path) -> SharedFiles:
    """Copies of the real shared files, so the real ones are never touched."""
    folder = tmp_path / "shared"
    folder.mkdir()
    copies = {
        "user_dictionary": Path("shared_data/user_dictionary.txt"),
        "sandhi_checked": DECON / "checked.csv",
        "sandhi_corrections": DECON / "manual_corrections.tsv",
        "variant_readings": DECON / "variant_readings.tsv",
        "spelling_mistakes": DECON / "spelling_mistakes.tsv",
        "tests_columns": ProjectPaths().internal_tests_path,
    }
    out: dict[str, Path] = {}
    for field_name, source in copies.items():
        target = folder / source.name
        shutil.copyfile(source, target)
        out[field_name] = target
    return SharedFiles(**out)


@pytest.fixture(autouse=True)
def no_editor(monkeypatch: pytest.MonkeyPatch) -> None:
    """A real editor open on the dev machine must not change these tests."""
    monkeypatch.setattr(contrib_pull, "editor_running", lambda: False)


class Setup:
    def __init__(self, tmp_path: Path, shared: SharedFiles) -> None:
        self.shared = shared
        self.server = tmp_path / "server"
        self.server.mkdir()
        self.repo = tmp_path / "repo"
        self.data = self.repo / "gui2" / "data"
        self.data.mkdir(parents=True)
        (self.data / "additions_added.json").write_text("[]")
        self.status_path = tmp_path / "logs" / "contrib_pull_status.txt"
        self.lock_path = tmp_path / "logs" / "contrib_pull.lock"
        self.tmp_path = tmp_path

    def go(self, now: datetime = DAY_ONE, dry_run: bool = False) -> Status:
        return run(
            f"{self.server}/",
            self.repo,
            self.shared,
            self.status_path,
            self.lock_path,
            now,
            dry_run,
        )

    def snapshot(self) -> dict[str, str]:
        """Hash of every file under the repo, the logs and the shared copies."""
        found: dict[str, str] = {}
        for folder in (
            self.repo,
            self.status_path.parent,
            self.shared.user_dictionary.parent,
        ):
            for path in sorted(folder.rglob("*")):
                # The empty lock file holds no state; the first run creates it.
                if path.is_file() and path.suffix != ".lock":
                    found[str(path)] = hashlib.sha1(path.read_bytes()).hexdigest()
        return found


@pytest.fixture
def setup(tmp_path: Path, shared: SharedFiles) -> Setup:
    return Setup(tmp_path, shared)


def put_good_files(folder: Path, user: str, word: str) -> None:
    (folder / f"additions_{user}.json").write_bytes(GOOD_CONTENT["additions"])
    (folder / f"checked_{user}.csv").write_text(f"{word}\n", encoding="utf-8")


def test_a_full_run_brings_the_files_and_merges_the_flag_lines(setup: Setup) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    status = setup.go()
    assert status.outcome == "pulled"
    assert status.last_success == "2026-11-04"
    assert (setup.data / "additions_alice.json").read_bytes() == GOOD_CONTENT[
        "additions"
    ]
    assert "zzpulltestword" in setup.shared.sandhi_checked.read_text(encoding="utf-8")
    assert status.lines_added == 1
    assert status.contributors == ["alice: pulled 2 files, 1 entries"]
    assert read_status(setup.status_path).last_success == "2026-11-04"


def test_a_second_run_the_same_day_does_nothing(setup: Setup) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    setup.go()
    before = setup.snapshot()
    assert setup.go().outcome == "skipped: already done today"
    assert setup.snapshot() == before


def test_an_open_editor_skips_the_run_and_changes_nothing(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    monkeypatch.setattr(contrib_pull, "editor_running", lambda: True)
    before = setup.snapshot()
    assert setup.go().outcome == "skipped: editor open"
    assert setup.snapshot() == before


def test_an_open_editor_stops_the_run_before_the_server_is_asked(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_listing(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]:
        raise AssertionError("the server was asked while the editor was open")

    monkeypatch.setattr(contrib_pull, "editor_running", lambda: True)
    monkeypatch.setattr(contrib_pull, "list_source", no_listing)
    assert setup.go().outcome == "skipped: editor open"


def editor_opens_at_check(number: int, monkeypatch: pytest.MonkeyPatch) -> None:
    """The editor is closed at the first `number - 1` checks and open at the
    check with this number (1 = gate, 2 = before copy in, 3 = before merge)."""
    calls: list[int] = []

    def stub() -> bool:
        calls.append(1)
        return len(calls) >= number

    monkeypatch.setattr(contrib_pull, "editor_running", stub)


def test_an_editor_that_opens_before_the_copy_in_leaves_gui2_data_alone(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    editor_opens_at_check(2, monkeypatch)
    before = setup.snapshot()
    assert setup.go().outcome == "skipped: editor open"
    assert setup.snapshot() == before


def test_an_editor_that_opens_before_the_merge_gives_a_partial_run(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    editor_opens_at_check(3, monkeypatch)
    checked_before = setup.shared.sandhi_checked.read_bytes()
    status = setup.go()
    assert status.outcome == "partial"
    assert status.last_success is None
    assert setup.shared.sandhi_checked.read_bytes() == checked_before
    assert (setup.data / "additions_alice.json").exists()


def test_a_bad_contributor_is_skipped_and_the_others_arrive(setup: Setup) -> None:
    put_good_files(setup.server, "bob", "zzbobword")
    (setup.server / "additions_alice.json").write_text("{broken")
    old_alice = b'{"alice_1": {"id": 1}}'
    (setup.data / "additions_alice.json").write_bytes(old_alice)
    status = setup.go()
    assert status.outcome == "pulled with problems"
    assert (setup.data / "additions_alice.json").read_bytes() == old_alice
    assert (setup.data / "additions_bob.json").exists()
    assert status.contributors[0].startswith("alice: skipped, additions_alice.json")
    assert status.last_success == "2026-11-04"


def test_a_crash_while_copying_in_keeps_the_old_last_success(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_status(setup.status_path, Status(last_success="2026-11-01"))
    put_good_files(setup.server, "alice", "zzpulltestword")

    def boom(scratch: Path, data_dir: Path) -> list[str]:
        raise OSError("disk full")

    monkeypatch.setattr(contrib_pull, "copy_in", boom)
    status = setup.go()
    assert status.outcome == "failed: disk full"
    assert read_status(setup.status_path).last_success == "2026-11-01"
    assert "failed" in setup.status_path.read_text(encoding="utf-8")


def test_a_dry_run_changes_no_file_and_keeps_last_success(setup: Setup) -> None:
    write_status(setup.status_path, Status(last_success="2026-11-01"))
    put_good_files(setup.server, "alice", "zzpulltestword")
    before = setup.snapshot()
    status = setup.go(dry_run=True)
    assert status.outcome == "dry run, nothing copied"
    assert status.contributors == ["alice: would copy 2 files, 1 entries"]
    assert status.last_success == "2026-11-01"
    assert setup.snapshot() == before


def test_a_held_lock_skips_the_run(setup: Setup) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    setup.lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(setup.lock_path, "a", encoding="utf-8") as other:
        fcntl.flock(other, fcntl.LOCK_EX)
        before = setup.snapshot()
        assert setup.go().outcome == "skipped: another run"
        assert setup.snapshot() == before


def test_the_notice_goes_out_from_22_30_on_a_failed_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    failed = Status(outcome="failed: boom")
    maybe_notify(failed, datetime(2026, 11, 4, 21, 59))
    assert sent == []
    maybe_notify(failed, datetime(2026, 11, 4, 22, 30))
    assert sent == ["failed: boom"]


@pytest.mark.parametrize("outcome", ["pulled", "skipped: editor open"])
def test_no_notice_for_a_good_or_skipped_run(
    monkeypatch: pytest.MonkeyPatch, outcome: str
) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    maybe_notify(Status(outcome=outcome), datetime(2026, 11, 4, 22, 30))
    assert sent == []


def test_a_notice_that_cannot_be_sent_is_noted_in_the_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(message: str) -> None:
        raise FileNotFoundError("notify-send")

    monkeypatch.setattr(contrib_pull, "notify", broken)
    status = Status(outcome="partial")
    maybe_notify(status, datetime(2026, 11, 4, 23, 0))
    assert status.notice_error is not None


def test_the_editor_open_skip_sends_a_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)

    contrib_pull.notify_editor_open(Status(outcome=contrib_pull.EDITOR_OPEN))

    assert sent == ["skipped: editor open"]


def test_a_failed_editor_open_notice_is_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(message: str) -> None:
        raise FileNotFoundError("notify-send")

    monkeypatch.setattr(contrib_pull, "notify", broken)

    contrib_pull.notify_editor_open(Status(outcome=contrib_pull.EDITOR_OPEN))


def _run_main(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: str, *argv: str
) -> list[str]:
    sent: list[str] = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["contrib_pull", *argv])
    monkeypatch.setattr(contrib_pull, "config_read", lambda *_: "user@host")
    monkeypatch.setattr(contrib_pull.SharedFiles, "default", lambda: None)
    monkeypatch.setattr(
        contrib_pull, "run", lambda *args, **kwargs: Status(outcome=outcome)
    )
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    contrib_pull.main()
    return sent


def test_main_sends_one_notice_for_an_editor_open_skip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    sent = _run_main(monkeypatch, tmp_path, "skipped: editor open")

    assert sent == ["skipped: editor open"]


@pytest.mark.parametrize(
    "outcome", ["skipped: already done today", "skipped: another run"]
)
def test_main_stays_silent_for_the_other_skips(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, outcome: str
) -> None:
    assert _run_main(monkeypatch, tmp_path, outcome) == []


def test_main_sends_no_notice_on_a_dry_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    assert _run_main(monkeypatch, tmp_path, "skipped: editor open", "--dry-run") == []


def test_a_missing_or_unreadable_status_file_means_no_earlier_success(
    tmp_path: Path,
) -> None:
    assert read_status(tmp_path / "none.txt").last_success is None
    garbage = tmp_path / "garbage.txt"
    garbage.write_bytes(b"\xff\xfe\x00")
    assert read_status(garbage).last_success is None
    garbage.write_text("last_success: not a date\n")
    assert read_status(garbage).last_success is None


def test_a_contributor_named_last_success_cannot_fake_the_date(tmp_path: Path) -> None:
    path = tmp_path / "status.txt"
    write_status(
        path, Status(outcome="partial", contributors=["last_success: 2 files"])
    )
    assert read_status(path).last_success is None


def test_a_flag_line_merged_on_day_one_is_not_merged_again_on_day_two(
    setup: Setup,
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    assert setup.go(DAY_ONE).lines_added == 1
    after_day_one = setup.shared.sandhi_checked.read_bytes()
    second = setup.go(DAY_TWO)
    assert second.outcome == "pulled"
    assert second.lines_added == 0
    assert setup.shared.sandhi_checked.read_bytes() == after_day_one


def test_a_failed_listing_names_no_secret(setup: Setup) -> None:
    status = run(
        f"{setup.tmp_path / 'nothing'}/",
        setup.repo,
        setup.shared,
        setup.status_path,
        setup.lock_path,
        DAY_ONE,
        False,
    )
    assert status.outcome.startswith("failed: rsync failed")


def test_redact_hides_the_ssh_target_and_the_key_path() -> None:
    text = (
        f"ssh: Could not resolve hostname epitaka.example: x; {contrib_pull.KEY_PATH}"
    )
    cleaned = redact(text, "root@epitaka.example:")
    assert "epitaka.example" not in cleaned
    assert str(contrib_pull.KEY_PATH) not in cleaned


def test_the_editor_is_a_process_with_an_argument_ending_in_gui2_main_py(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.undo()
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)", "gui2/main.py"]
    )
    try:
        assert editor_running() is True
    finally:
        child.kill()
        child.wait()


@pytest.mark.parametrize("kind", ["variant_readings", "spelling_mistakes"])
def test_a_two_column_file_without_its_header_is_refused(
    tmp_path: Path, kind: str
) -> None:
    assert check_content(write(tmp_path, kind, b"abc\tabd\r\n"), kind) == (
        "first line is not the header"
    )


@pytest.mark.parametrize("line", [b"abc\t\r\n", b"\tabd\r\n"])
def test_a_two_column_line_with_an_empty_field_is_refused(
    tmp_path: Path, line: bytes
) -> None:
    content = b"variant\tmain\r\n" + line
    assert check_content(
        write(tmp_path, "variant_readings", content), "variant_readings"
    )


def test_a_problem_pull_is_announced_at_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    maybe_notify(Status(outcome="pulled with problems"), datetime(2026, 11, 4, 9, 0))
    assert sent == ["pulled with problems"]


def test_a_failed_run_before_22_30_is_not_announced(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []
    monkeypatch.setattr(contrib_pull, "notify", sent.append)
    maybe_notify(Status(outcome="failed: x"), datetime(2026, 11, 4, 9, 0))
    assert sent == []


class FakeRun:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []
        self.timeouts: list[object] = []

    def __call__(
        self, command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        self.timeouts.append(kwargs.get("timeout"))
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_a_remote_source_gets_the_fixed_ssh_options_and_a_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeRun()
    monkeypatch.setattr(contrib_pull.subprocess, "run", fake)
    list_source("root@host.example:", SSH_OPTIONS)
    command = fake.commands[0]
    assert command[:2] == ["rsync", "-e"]
    for option in ("BatchMode=yes", "IdentitiesOnly=yes", "ForwardAgent=no"):
        assert option in command[2]
    assert "--timeout=60" in command
    assert fake.timeouts == [contrib_pull.RSYNC_DEADLINE]
    assert command[-1] == "root@host.example:"


def test_a_local_source_gets_no_ssh_option(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeRun()
    monkeypatch.setattr(contrib_pull.subprocess, "run", fake)
    list_source("/some/folder/", [])
    assert "-e" not in fake.commands[0]


def test_an_rsync_that_hangs_becomes_a_failed_run(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    def hang(command: list[str], **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(command, 300)

    monkeypatch.setattr(contrib_pull.subprocess, "run", hang)
    assert setup.go().outcome == "failed: rsync gave no answer in 300 s"


def test_a_file_name_that_is_not_utf8_is_ignored_and_counted(setup: Setup) -> None:
    (setup.server / os.fsdecode(b"additions_\xff.json")).write_bytes(b"{}")
    put_good_files(setup.server, "alice", "zzpulltestword")
    status = setup.go()
    assert status.outcome == "pulled"
    assert status.ignored_names == 1
    assert status.contributors == ["alice: pulled 2 files, 1 entries"]


def test_a_corrupt_merged_lines_log_becomes_a_failed_run(setup: Setup) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    (setup.data / "contrib_lines_merged.json").write_text("{broken")
    status = setup.go()
    assert status.outcome.startswith("failed")
    assert status.last_success is None
    assert not (setup.data / "additions_alice.json").exists()


def test_a_json_error_in_the_merge_becomes_a_failed_run(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")

    def broken(*args: object, **kwargs: object) -> None:
        raise json.JSONDecodeError("bad log", "{", 1)

    monkeypatch.setattr(contrib_pull, "merge_all", broken)
    status = setup.go()
    assert status.outcome.startswith("failed: bad log")
    assert status.last_success is None


def test_a_dry_run_does_not_log_ignored_names(setup: Setup) -> None:
    (setup.server / "additions_Alice.json").write_bytes(b"{}")
    status = setup.go(dry_run=True)
    assert status.ignored_names == 1
    assert not setup.status_path.with_name("contrib_pull.log").exists()


def test_the_merged_lines_log_stops_a_line_the_maintainer_deleted_from_coming_back(
    setup: Setup,
) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    setup.go(DAY_ONE)
    shared = setup.shared.sandhi_checked
    shared.write_text(
        shared.read_text(encoding="utf-8").replace("zzpulltestword\n", ""),
        encoding="utf-8",
    )
    setup.go(DAY_TWO)
    assert "zzpulltestword" not in shared.read_text(encoding="utf-8")


@pytest.mark.parametrize("line", [b"a\tb\tc\n", b"abc\n", b"abc\t\n", b"\tabc\n"])
def test_a_manual_correction_line_without_two_filled_columns_is_refused(
    tmp_path: Path, line: bytes
) -> None:
    assert check_content(
        write(tmp_path, "manual_corrections", line), "manual_corrections"
    ) == ("line without exactly 2 filled columns")


@pytest.mark.parametrize("kind", ["checked", "user_dictionary"])
def test_a_one_word_file_with_a_tab_is_refused(tmp_path: Path, kind: str) -> None:
    assert check_content(write(tmp_path, kind, b"abc\tdef\n"), kind) == (
        "line has a tab in a one-column file"
    )


@pytest.mark.parametrize(
    "entry_id", ["9" * 5000, "\u00b2", True, 1.5, None, [1], "12345678901234"]
)
def test_an_entry_id_that_is_not_a_plain_number_is_refused(
    tmp_path: Path, entry_id: object
) -> None:
    content = json.dumps({"alice_1": {"id": entry_id}}).encode()
    assert check_content(write(tmp_path, "additions", content), "additions") == (
        "an entry id is not a plain number"
    )


@pytest.mark.parametrize("entry_id", [10000002, "10000002", 0])
def test_a_plain_entry_id_passes(tmp_path: Path, entry_id: object) -> None:
    content = json.dumps({"alice_1": {"id": entry_id}}).encode()
    assert check_content(write(tmp_path, "additions", content), "additions") is None


def test_an_entry_without_an_id_passes(tmp_path: Path) -> None:
    content = json.dumps({"alice_1": {"lemma_1": "x"}}).encode()
    assert check_content(write(tmp_path, "additions", content), "additions") is None


def test_a_huge_id_skips_that_contributor_and_not_the_run(setup: Setup) -> None:
    put_good_files(setup.server, "bob", "zzbobword")
    huge = json.dumps({"alice_1": {"id": "9" * 5000}})
    (setup.server / "additions_alice.json").write_text(huge)
    status = setup.go()
    assert status.outcome == "pulled with problems"
    assert (setup.data / "additions_bob.json").exists()
    assert not (setup.data / "additions_alice.json").exists()


def test_a_failure_text_with_extra_lines_stays_one_short_line(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    hostile = "x\nlast_success: 2099-01-01\n" + "y" * 1000

    def listing(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]:
        raise PullError(hostile)

    monkeypatch.setattr(contrib_pull, "list_source", listing)
    status = setup.go()
    assert "\n" not in status.outcome
    assert len(status.outcome) <= len("failed: ") + contrib_pull.MAX_OUTCOME_LENGTH
    assert read_status(setup.status_path).last_success is None


def test_the_first_last_success_line_wins(tmp_path: Path) -> None:
    path = tmp_path / "status.txt"
    path.write_text("last_success: 2026-11-04\nlast_success: 2099-01-01\n")
    assert read_status(path).last_success == "2026-11-04"


def test_a_remote_run_picks_the_ssh_options_and_a_local_run_none(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[list[str]] = []

    def listing(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]:
        seen.append(ssh)
        return []

    monkeypatch.setattr(contrib_pull, "list_source", listing)
    setup.go()
    run(
        "root@host.example:",
        setup.repo,
        setup.shared,
        setup.status_path,
        setup.lock_path,
        DAY_TWO,
        False,
    )
    assert seen == [[], SSH_OPTIONS]


def test_a_failed_remote_run_writes_no_target_and_no_key_path(
    setup: Setup, monkeypatch: pytest.MonkeyPatch
) -> None:
    def listing(source: str, ssh: list[str]) -> list[tuple[str, int, bool]]:
        raise PullError(
            f"ssh: Could not resolve hostname host.example: {contrib_pull.KEY_PATH}"
        )

    monkeypatch.setattr(contrib_pull, "list_source", listing)
    status = run(
        "root@host.example:",
        setup.repo,
        setup.shared,
        setup.status_path,
        setup.lock_path,
        DAY_ONE,
        False,
    )
    written = (
        setup.status_path.read_text()
        + setup.status_path.with_name("contrib_pull.log").read_text()
    )
    for text in (status.outcome, status.text(), written):
        assert "host.example" not in text
        assert str(contrib_pull.KEY_PATH) not in text
    assert status.outcome.startswith("failed: ssh: Could not resolve hostname")


def test_a_dry_run_ignores_the_already_done_today_gate(setup: Setup) -> None:
    put_good_files(setup.server, "alice", "zzpulltestword")
    write_status(setup.status_path, Status(last_success=DAY_ONE.date().isoformat()))
    assert setup.go(DAY_ONE, dry_run=True).outcome == "dry run, nothing copied"


def test_an_empty_server_folder_is_not_reported_as_a_plain_success(
    setup: Setup,
) -> None:
    status = setup.go()
    assert status.outcome == "pulled, no contributor files"
    assert status.last_success == "2026-11-04"


def test_main_without_the_ssh_setting_stops_with_a_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(contrib_pull, "config_read", lambda section, option: "")
    monkeypatch.setattr(sys, "argv", ["contrib_pull.py"])
    assert contrib_pull.main() == 1
    assert "[dpd_contributor_server] ssh is not set" in capsys.readouterr().err


def test_main_writes_a_failed_notice_back_to_the_status_file(
    setup: Setup,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_notify(message: str) -> None:
        raise FileNotFoundError("notify-send")

    def fake_run(*args: object, **kwargs: object) -> Status:
        status = Status(outcome="failed: boom", finished="x")
        write_status(setup.status_path, status)
        return status

    monkeypatch.chdir(setup.tmp_path)
    monkeypatch.setattr(sys, "argv", ["contrib_pull.py"])
    monkeypatch.setattr(contrib_pull, "config_read", lambda section, option: "u@h")
    monkeypatch.setattr(contrib_pull, "run", fake_run)
    monkeypatch.setattr(contrib_pull, "notify", broken_notify)
    monkeypatch.setattr(contrib_pull, "NOTICE_FROM", time(0, 0))
    monkeypatch.setattr(contrib_pull.SharedFiles, "default", lambda: setup.shared)
    assert contrib_pull.main() == 1
    assert "notice_error:" in setup.status_path.read_text()
    assert "outcome: failed: boom" in capsys.readouterr().out
