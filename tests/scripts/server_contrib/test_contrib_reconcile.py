"""Reconcile against main's logs (plan 5.1; Phase 4 case rows 1-9, 17, 18)."""

import json
from pathlib import Path

import pytest

from gui2.database_manager import CONTRIB_ID_BASE
from scripts.server_contrib.contrib_reconcile import (
    load_json_dict,
    load_processed,
    reconcile_all,
    reconcile_entries,
    reconcile_exception_lines,
    reconcile_lines,
    write_json_dict,
)
from tools.contrib_entry import entry_hash


def entry(meaning: str, id_: int = 1) -> dict:
    return {"id": id_, "meaning_1": meaning}


def log_row(key: str, value: dict, **extra: object) -> dict:
    return {"_source_key": key, "_source_hash": entry_hash(value), **extra}


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A project root whose gui2/data holds main's logs."""
    root = tmp_path / "main"
    (root / "gui2" / "data").mkdir(parents=True)
    return root


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    path = tmp_path / "server_data"
    path.mkdir()
    return path


def write_log(project: Path, name: str, rows: list[dict]) -> None:
    (project / "gui2" / "data" / name).write_text(json.dumps(rows), encoding="utf-8")


def write_merged(project: Path, merged: dict[str, list[str]]) -> None:
    (project / "gui2" / "data" / "contrib_lines_merged.json").write_text(
        json.dumps(merged), encoding="utf-8"
    )


class TestReconcileEntries:
    def test_not_processed_is_kept(self):  # rows 1, 2
        local = {"alice_1": entry("a")}
        assert reconcile_entries(local, set()) == local

    def test_processed_is_dropped(self):  # row 3
        local = {"alice_1": entry("a"), "alice_2": entry("b")}
        processed = {("alice_1", entry_hash(entry("a")))}
        assert reconcile_entries(local, processed) == {"alice_2": entry("b")}

    def test_re_edit_after_processing_is_kept(self):  # rows 5, 6
        processed = {("alice_1", entry_hash(entry("v1")))}
        local = {"alice_1": entry("v2")}
        assert reconcile_entries(local, processed) == local

    def test_same_hash_other_key_is_kept(self):  # row 7
        processed = {("alice_1", entry_hash(entry("a")))}
        local = {"bob_1": entry("a")}
        assert reconcile_entries(local, processed) == local


class TestReconcileLines:
    def test_merged_lines_go_and_each_line_keeps_its_ending(self):
        lines = ["one\r\n", "two\n", "three"]
        assert reconcile_lines(lines, {"two"}, keep_header=False) == [
            "one\r\n",
            "three",
        ]

    def test_crlf_line_matches_the_logged_line(self):  # row 8
        assert reconcile_lines(["a\tb\r\n"], {"a\tb"}, keep_header=False) == []

    def test_header_stays_and_first_pair_is_kept(self):  # row 8 (F1)
        lines = ["variant\tmain\r\n", "k\tv\r\n"]
        merged = {"variant\tmain", "other\tpair"}
        assert reconcile_lines(lines, merged, keep_header=True) == lines

    def test_a_logged_line_is_dropped_even_if_main_deleted_it(self):  # row 9
        assert reconcile_lines(["gone\n"], {"gone"}, keep_header=False) == []

    def test_unlogged_line_is_kept(self):  # row 9: a changed value is a new line
        assert reconcile_lines(["k\tv2\n"], {"k\tv1"}, keep_header=False) == ["k\tv2\n"]


class TestExceptionLines:
    def test_reserved_id_goes_once_no_addition_holds_it(self):  # row 18
        reserved = CONTRIB_ID_BASE + 1
        lines = [f"test\t{reserved}\n", "test\t5\n"]
        assert reconcile_exception_lines(lines, set(), held_ids=set()) == ["test\t5\n"]

    def test_reserved_id_stays_while_an_addition_holds_it(self):
        reserved = CONTRIB_ID_BASE + 1
        lines = [f"test\t{reserved}\n"]
        assert reconcile_exception_lines(lines, set(), held_ids={reserved}) == lines

    def test_merged_exception_line_goes(self):
        assert reconcile_exception_lines(["test\t5\n"], {"test\t5"}, set()) == []


class TestLoadHelpers:
    def test_missing_file_is_empty(self, tmp_path: Path):
        assert load_json_dict(tmp_path / "nope.json") == {}
        assert load_processed(tmp_path / "nope.json") == set()

    def test_corrupt_file_raises(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json")
        with pytest.raises(RuntimeError):
            load_json_dict(bad)
        with pytest.raises(RuntimeError):
            load_processed(bad)

    def test_write_json_dict_is_atomic_and_round_trips(self, tmp_path: Path):
        path = tmp_path / "sub" / "a.json"
        write_json_dict(path, {"k": {"x": "ü"}})
        assert load_json_dict(path) == {"k": {"x": "ü"}}
        write_json_dict(path, {})
        assert path.read_text() == "{}"
        assert not list(path.parent.glob("*.tmp"))

    def test_rows_without_a_source_pair_are_ignored(self, tmp_path: Path):
        path = tmp_path / "log.json"
        path.write_text(json.dumps([{"lemma_1": "x"}, log_row("a_1", entry("a"))]))
        assert load_processed(path) == {("a_1", entry_hash(entry("a")))}


class TestReconcileAll:
    def test_additions_processed_rejected_and_pending(
        self, project: Path, data_dir: Path
    ):  # rows 1-4
        accepted, rejected, pending = entry("a", 1), entry("b", 2), entry("c", 3)
        write_json_dict(
            data_dir / "additions_alice.json",
            {"alice_1": accepted, "alice_2": rejected, "alice_3": pending},
        )
        write_log(
            project,
            "additions_added.json",
            [
                log_row("alice_1", accepted, lemma_1="a"),
                log_row("alice_2", rejected, _rejected=True),
            ],
        )

        remaining = reconcile_all(project, data_dir)

        assert load_json_dict(data_dir / "additions_alice.json") == {"alice_3": pending}
        assert remaining["additions_alice.json"] == 1

    def test_emptied_file_is_written_not_deleted(self, project: Path, data_dir: Path):
        only = entry("a")
        write_json_dict(data_dir / "corrections_alice.json", {"alice_1": only})
        write_log(project, "corrections_added.json", [log_row("alice_1", only)])

        reconcile_all(project, data_dir)

        assert (data_dir / "corrections_alice.json").read_text() == "{}"

    def test_missing_logs_drop_nothing(self, project: Path, data_dir: Path):
        write_json_dict(data_dir / "additions_alice.json", {"alice_1": entry("a")})
        (data_dir / "checked_alice.csv").write_text("word\n")

        reconcile_all(project, data_dir)

        assert load_json_dict(data_dir / "additions_alice.json") == {
            "alice_1": entry("a")
        }
        assert (data_dir / "checked_alice.csv").read_text() == "word\n"

    def test_own_variant_file_keeps_header_and_first_pair(
        self, project: Path, data_dir: Path
    ):  # row 8
        path = data_dir / "variant_readings_alice.tsv"
        path.write_bytes(b"variant\tmain\r\nk1\tv1\r\nk2\tv2\r\n")
        write_merged(
            project,
            {"variant_readings_alice.tsv": ["k2\tv2"], "other_alice.tsv": ["k1\tv1"]},
        )

        remaining = reconcile_all(project, data_dir)

        assert path.read_bytes() == b"variant\tmain\r\nk1\tv1\r\n"
        assert remaining["variant_readings_alice.tsv"] == 2

    def test_lines_logged_for_another_file_are_not_dropped(
        self, project: Path, data_dir: Path
    ):  # row 7
        (data_dir / "checked_alice.csv").write_text("w1\nw2\n")
        (data_dir / "checked_bob.csv").write_text("w1\nw2\n")
        write_merged(project, {"checked_alice.csv": ["w1"]})

        reconcile_all(project, data_dir)

        assert (data_dir / "checked_alice.csv").read_text() == "w2\n"
        assert (data_dir / "checked_bob.csv").read_text() == "w1\nw2\n"

    def test_a_flag_line_deleted_from_main_stays_dropped(
        self, project: Path, data_dir: Path
    ):  # row 9
        (data_dir / "user_dictionary_alice.txt").write_text("gone\nkeep\n")
        write_merged(project, {"user_dictionary_alice.txt": ["gone"]})

        reconcile_all(project, data_dir)

        assert (data_dir / "user_dictionary_alice.txt").read_text() == "keep\n"

    def test_reserved_exception_goes_when_its_addition_is_processed(
        self, project: Path, data_dir: Path
    ):  # row 18
        reserved = CONTRIB_ID_BASE + 1
        word = entry("a", reserved)
        write_json_dict(data_dir / "additions_alice.json", {"alice_1": word})
        (data_dir / "db_test_exceptions_alice.tsv").write_text(
            f"some_test\t{reserved}\nsome_test\t7\n"
        )
        write_log(project, "additions_added.json", [log_row("alice_1", word)])

        reconcile_all(project, data_dir)

        assert (data_dir / "db_test_exceptions_alice.tsv").read_text() == (
            "some_test\t7\n"
        )

    def test_reserved_exception_stays_while_the_addition_is_pending(
        self, project: Path, data_dir: Path
    ):
        reserved = CONTRIB_ID_BASE + 1
        write_json_dict(
            data_dir / "additions_alice.json", {"alice_1": entry("a", reserved)}
        )
        text = f"some_test\t{reserved}\n"
        (data_dir / "db_test_exceptions_alice.tsv").write_text(text)

        reconcile_all(project, data_dir)

        assert (data_dir / "db_test_exceptions_alice.tsv").read_text() == text

    def test_entry_of_a_word_deleted_on_main_stays_until_rejected(
        self, project: Path, data_dir: Path
    ):  # row 17: a correction for a deleted word is not in any log
        write_json_dict(data_dir / "corrections_alice.json", {"alice_9": entry("a", 9)})

        reconcile_all(project, data_dir)

        assert list(load_json_dict(data_dir / "corrections_alice.json")) == ["alice_9"]

    def test_review_logs_and_session_files_are_not_touched(
        self, project: Path, data_dir: Path
    ):
        for name in ("additions_added_alice.json", "history_alice.json"):
            (data_dir / name).write_text("not json at all")

        reconcile_all(project, data_dir)

        assert (data_dir / "history_alice.json").read_text() == "not json at all"

    def test_a_corrupt_contributor_file_aborts_without_writing(
        self, project: Path, data_dir: Path
    ):
        (data_dir / "additions_alice.json").write_text("{broken")

        with pytest.raises(RuntimeError):
            reconcile_all(project, data_dir)

        assert (data_dir / "additions_alice.json").read_text() == "{broken"
