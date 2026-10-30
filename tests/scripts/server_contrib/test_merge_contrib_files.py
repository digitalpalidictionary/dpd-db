"""merge_contrib_files on copies of the real shared files."""

import shutil
from pathlib import Path

import pytest

from db_tests.db_tests_manager import DbTestManager
from gui2.database_manager import CONTRIB_ID_BASE
from scripts.server_contrib.merge_contrib_files import (
    SharedFiles,
    merge_all,
    read_merged_log,
    write_merged_log,
)
from tools.paths import ProjectPaths

DECON = Path("shared_data/deconstructor")


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
    for field, source in copies.items():
        target = folder / source.name
        shutil.copyfile(source, target)
        out[field] = target
    return SharedFiles(**out)


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    path = tmp_path / "data"
    path.mkdir()
    return path


def _bytes(path: Path) -> bytes:
    return path.read_bytes()


def test_user_dictionary_word_lands_in_sorted_place_once(
    shared: SharedFiles, data_dir: Path
) -> None:
    before = _bytes(shared.user_dictionary).decode().split("\n")[:-1]
    (data_dir / "user_dictionary_alice.txt").write_text(
        "zzzqword\nAaaqword\n" + before[10] + "\n", encoding="utf-8"
    )

    report = merge_all(data_dir, shared)

    assert report["user_dictionary_alice.txt"] == ["Aaaqword", "zzzqword"]
    after = _bytes(shared.user_dictionary).decode().split("\n")[:-1]
    assert after == sorted(
        before + ["zzzqword", "Aaaqword"], key=lambda w: (w.lower(), w)
    )
    assert len(after) == len(before) + 2
    assert merge_all(data_dir, shared)["user_dictionary_alice.txt"] == []


def test_checked_and_corrections_are_appended_after_the_old_bytes(
    shared: SharedFiles, data_dir: Path
) -> None:
    old_checked = _bytes(shared.sandhi_checked)
    old_corrections = _bytes(shared.sandhi_corrections)
    known_checked = old_checked.decode().split("\n")[5].rstrip("\r")
    (data_dir / "checked_alice.csv").write_text(
        f"qqsandhione\n{known_checked}\r\nqqsandhitwo\n", encoding="utf-8", newline=""
    )
    (data_dir / "manual_corrections_alice.tsv").write_text(
        "qqsandhione\tqq + sandhione\n", encoding="utf-8"
    )

    report = merge_all(data_dir, shared)

    assert report["checked_alice.csv"] == ["qqsandhione", "qqsandhitwo"]
    assert report["manual_corrections_alice.tsv"] == ["qqsandhione\tqq + sandhione"]
    assert _bytes(shared.sandhi_checked) == old_checked + b"qqsandhione\nqqsandhitwo\n"
    assert (
        _bytes(shared.sandhi_corrections)
        == old_corrections + b"qqsandhione\tqq + sandhione\n"
    )
    assert merge_all(data_dir, shared)["checked_alice.csv"] == []
    assert merge_all(data_dir, shared)["manual_corrections_alice.tsv"] == []


@pytest.mark.parametrize(
    ("contrib_name", "field", "header"),
    [
        ("variant_readings_alice.tsv", "variant_readings", "variant\tmain"),
        ("spelling_mistakes_alice.tsv", "spelling_mistakes", "mistake\tcorrection"),
    ],
)
def test_two_column_files_keep_header_crlf_and_order(
    shared: SharedFiles, data_dir: Path, contrib_name: str, field: str, header: str
) -> None:
    path: Path = getattr(shared, field)
    old = _bytes(path)
    old_rows = old.decode().split("\r\n")[:-1]
    second_key, second_value = old_rows[2].split("\t")
    (data_dir / contrib_name).write_text(
        f"{header}\r\nqqnew\tqqmain\r\n{second_key}\tchanged\r\n{old_rows[1]}\r\n",
        encoding="utf-8",
        newline="",
    )

    report = merge_all(data_dir, shared)

    assert report[contrib_name] == [
        "qqnew\tqqmain",
        f"{second_key}\tchanged (was {second_value})",
    ]
    new_rows = _bytes(path).decode().split("\r\n")[:-1]
    assert new_rows[0] == header
    assert new_rows[2] == f"{second_key}\tchanged"
    assert new_rows[-1] == "qqnew\tqqmain"
    assert len(new_rows) == len(old_rows) + 1
    assert b"\n" not in _bytes(path).replace(b"\r\n", b"")
    assert merge_all(data_dir, shared)[contrib_name] == []


def test_test_exception_lands_in_the_named_tests_list(
    shared: SharedFiles, data_dir: Path
) -> None:
    manager = DbTestManager()
    manager.tests_path = shared.tests_columns
    tests = manager.load_tests()
    target = tests[3]
    new_id = max(target.exceptions, default=0) + 1
    (data_dir / "db_test_exceptions_alice.tsv").write_text(
        f"{target.test_name}\t{new_id}\nno such test\t5\n", encoding="utf-8"
    )

    report = merge_all(data_dir, shared)

    assert report["db_test_exceptions_alice.tsv"] == [
        f"{target.test_name}\t{new_id}",
        "skipped (no such test or bad id): no such test\t5",
    ]
    after = {t.test_name: t.exceptions for t in manager.load_tests()}
    before = {t.test_name: t.exceptions for t in tests}
    assert after.pop(target.test_name) == sorted(
        [*before.pop(target.test_name), new_id]
    )
    assert after == before
    assert merge_all(data_dir, shared)["db_test_exceptions_alice.tsv"] == [
        "skipped (no such test or bad id): no such test\t5"
    ]


def test_a_line_removed_from_the_shared_file_is_not_added_again(
    shared: SharedFiles, data_dir: Path, tmp_path: Path
) -> None:
    log_path = tmp_path / "log" / "contrib_lines_merged.json"
    (data_dir / "checked_alice.csv").write_text("qqsandhione\n", encoding="utf-8")
    assert merge_all(data_dir, shared, log_path)["checked_alice.csv"] == ["qqsandhione"]
    shared.sandhi_checked.write_bytes(
        _bytes(shared.sandhi_checked).replace(b"qqsandhione\n", b"")
    )
    after_delete = _bytes(shared.sandhi_checked)

    assert merge_all(data_dir, shared, log_path)["checked_alice.csv"] == []
    assert _bytes(shared.sandhi_checked) == after_delete
    assert read_merged_log(log_path) == {"checked_alice.csv": ["qqsandhione"]}


def test_a_variant_value_changed_on_main_is_not_changed_back(
    shared: SharedFiles, data_dir: Path, tmp_path: Path
) -> None:
    log_path = tmp_path / "contrib_lines_merged.json"
    (data_dir / "variant_readings_alice.tsv").write_text(
        "variant\tmain\r\nqqnew\tqqone\r\n", encoding="utf-8", newline=""
    )
    merge_all(data_dir, shared, log_path)
    changed = _bytes(shared.variant_readings).replace(b"qqnew\tqqone", b"qqnew\tqqtwo")
    shared.variant_readings.write_bytes(changed)

    assert merge_all(data_dir, shared, log_path)["variant_readings_alice.tsv"] == []
    assert _bytes(shared.variant_readings) == changed
    assert read_merged_log(log_path) == {"variant_readings_alice.tsv": ["qqnew\tqqone"]}


def test_a_reserved_id_exception_is_reported_not_merged_or_logged(
    shared: SharedFiles, data_dir: Path, tmp_path: Path
) -> None:
    log_path = tmp_path / "contrib_lines_merged.json"
    target = DbTestManager()
    target.tests_path = shared.tests_columns
    test_name = target.load_tests()[3].test_name
    line = f"{test_name}\t{CONTRIB_ID_BASE + 1}"
    (data_dir / "db_test_exceptions_alice.tsv").write_text(
        f"{line}\n", encoding="utf-8"
    )
    before = _bytes(shared.tests_columns)

    report = merge_all(data_dir, shared, log_path)

    assert report["db_test_exceptions_alice.tsv"] == [
        f"skipped (reserved id, means nothing on main): {line}"
    ]
    assert _bytes(shared.tests_columns) == before
    assert read_merged_log(log_path) == {"db_test_exceptions_alice.tsv": []}


def test_the_log_is_written_in_sorted_order(tmp_path: Path) -> None:
    log_path = tmp_path / "contrib_lines_merged.json"
    write_merged_log(log_path, {"b.csv": ["zz", "aa", "aa"], "a.csv": ["x"]})
    assert list(read_merged_log(log_path).items()) == [
        ("a.csv", ["x"]),
        ("b.csv", ["aa", "zz"]),
    ]


def test_no_contributor_files_means_an_empty_report(
    shared: SharedFiles, data_dir: Path
) -> None:
    assert merge_all(data_dir, shared) == {}
