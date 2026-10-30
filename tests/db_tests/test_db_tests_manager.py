"""Tests for the core (DB-free) logic of DbTestManager, the GUI's own
internal DB-integrity test runner."""

import hashlib
import shutil
from pathlib import Path

import pytest

from db.models import DpdHeadword
from db_tests.db_tests_manager import DbTestManager, InternalTestRow


def _test_row(**overrides) -> InternalTestRow:
    defaults: dict = dict(
        test_name="t",
        search_column_1="",
        search_sign_1="",
        search_string_1="",
        search_column_2="",
        search_sign_2="",
        search_string_2="",
        search_column_3="",
        search_sign_3="",
        search_string_3="",
        search_column_4="",
        search_sign_4="",
        search_string_4="",
        search_column_5="",
        search_sign_5="",
        search_string_5="",
        search_column_6="",
        search_sign_6="",
        search_string_6="",
        error_column="commentary",
        exceptions=[],
        iterations=10,
        display_1="lemma_1",
        display_2="grammar",
        display_3="commentary",
    )
    defaults.update(overrides)
    return InternalTestRow(**defaults)


def _headword(id: int = 1, commentary: str = "", meaning_1: str = "") -> DpdHeadword:
    hw = DpdHeadword()
    hw.id = id
    hw.commentary = commentary
    hw.meaning_1 = meaning_1
    return hw


@pytest.fixture
def manager() -> DbTestManager:
    """DbTestManager bypassing __init__ (no CSV/DB I/O)."""
    return object.__new__(DbTestManager)


class TestIntegrityCheck:
    def test_valid_row_passes(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary", search_sign_1="contains", search_string_1="//"
        )
        manager.internal_tests_list = [row]
        ok, failures = manager.integrity_check()
        assert ok is True
        assert failures == []

    def test_invalid_column_name_fails(self, manager: DbTestManager):
        row = _test_row(search_column_1="not_a_real_column")
        manager.internal_tests_list = [row]
        ok, failures = manager.integrity_check()
        assert ok is False
        assert len(failures) == 1
        assert failures[0].invalid_field_name == "search_column_1"
        assert failures[0].invalid_value == "not_a_real_column"

    def test_invalid_sign_fails(self, manager: DbTestManager):
        row = _test_row(search_column_1="commentary", search_sign_1="banana")
        manager.internal_tests_list = [row]
        ok, failures = manager.integrity_check()
        assert ok is False
        assert len(failures) == 1
        assert failures[0].invalid_field_name == "search_sign_1"
        assert failures[0].invalid_value == "banana"

    def test_empty_column_and_sign_are_valid(self, manager: DbTestManager):
        row = _test_row()
        manager.internal_tests_list = [row]
        ok, failures = manager.integrity_check()
        assert ok is True
        assert failures == []


class TestErrorTestEachSingleRow:
    def test_contains_match_flags_error(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary", search_sign_1="contains", search_string_1="//"
        )
        hw = _headword(id=1, commentary="foo // bar")
        assert manager.error_test_each_single_row(row, hw) is True

    def test_contains_no_match_is_not_an_error(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary", search_sign_1="contains", search_string_1="//"
        )
        hw = _headword(id=2, commentary="no slashes")
        assert manager.error_test_each_single_row(row, hw) is False

    def test_exception_id_never_errors(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary",
            search_sign_1="contains",
            search_string_1="//",
            exceptions=[1],
        )
        hw = _headword(id=1, commentary="foo // bar")
        assert manager.error_test_each_single_row(row, hw) is False

    def test_multiple_criteria_are_anded_all_true(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary",
            search_sign_1="is not empty",
            search_string_1="-",
            search_column_2="meaning_1",
            search_sign_2="is empty",
            search_string_2="-",
        )
        hw = _headword(id=3, commentary="something", meaning_1="")
        assert manager.error_test_each_single_row(row, hw) is True

    def test_multiple_criteria_are_anded_one_false(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary",
            search_sign_1="is not empty",
            search_string_1="-",
            search_column_2="meaning_1",
            search_sign_2="is empty",
            search_string_2="-",
        )
        hw = _headword(id=4, commentary="something", meaning_1="has meaning")
        assert manager.error_test_each_single_row(row, hw) is False


class TestRunTestOnAllDbEntries:
    def test_returns_only_failing_headwords(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary", search_sign_1="contains", search_string_1="//"
        )
        h1 = _headword(id=1, commentary="foo // bar")
        h2 = _headword(id=2, commentary="no slashes")
        result = manager.run_test_on_all_db_entries(row, [h1, h2])
        assert [hw.id for hw in result] == [1]

    def test_no_failures_returns_empty_list(self, manager: DbTestManager):
        row = _test_row(
            search_column_1="commentary", search_sign_1="contains", search_string_1="//"
        )
        h1 = _headword(id=1, commentary="clean")
        result = manager.run_test_on_all_db_entries(row, [h1])
        assert result == []


class TestOwnExceptions:
    """A contributor's exceptions go to their own file, never the shared TSV."""

    @pytest.fixture
    def own_manager(self, tmp_path: Path) -> DbTestManager:
        own_path = tmp_path / "db_test_exceptions_alice.tsv"
        manager = DbTestManager(own_path)
        # Work on a copy so a regression cannot touch the real tests file.
        shared_copy = tmp_path / "db_tests_columns.tsv"
        shutil.copyfile(manager.tests_path, shared_copy)
        manager.tests_path = shared_copy
        manager.internal_tests_list = manager.load_tests()
        return manager

    def test_add_exception_writes_own_file_only(
        self, own_manager: DbTestManager
    ) -> None:
        shared_before = hashlib.sha256(own_manager.tests_path.read_bytes()).digest()
        test = own_manager.internal_tests_list[0]
        new_id = max(test.exceptions, default=0) + 1

        assert own_manager.add_exception(test.test_name, new_id) is True

        assert own_manager.own_exceptions_path is not None
        assert own_manager.own_exceptions_path.read_text(encoding="utf-8") == (
            f"{test.test_name}\t{new_id}\n"
        )
        shared_after = hashlib.sha256(own_manager.tests_path.read_bytes()).digest()
        assert shared_after == shared_before

    def test_next_load_treats_the_id_as_an_exception(
        self, own_manager: DbTestManager
    ) -> None:
        test = own_manager.internal_tests_list[0]
        new_id = max(test.exceptions, default=0) + 1
        own_manager.add_exception(test.test_name, new_id)

        reloaded = {t.test_name: t for t in own_manager.load_tests()}

        assert new_id in reloaded[test.test_name].exceptions

    def test_unknown_test_name_and_junk_lines_are_ignored(
        self, own_manager: DbTestManager
    ) -> None:
        assert own_manager.own_exceptions_path is not None
        own_manager.own_exceptions_path.write_text(
            "no such test\t5\nbroken line\n", encoding="utf-8"
        )

        own_manager.load_tests()

    def test_primary_still_writes_the_shared_file(self, tmp_path: Path) -> None:
        manager = DbTestManager()
        shared_copy = tmp_path / "db_tests_columns.tsv"
        shutil.copyfile(manager.tests_path, shared_copy)
        manager.tests_path = shared_copy
        manager.internal_tests_list = manager.load_tests()
        test = manager.internal_tests_list[0]
        new_id = max(test.exceptions, default=0) + 1

        manager.add_exception(test.test_name, new_id)

        saved = {t.test_name: t for t in manager.load_tests()}
        assert new_id in saved[test.test_name].exceptions
