"""Tests for the core (DB-free) logic of DbTestManager, the GUI's own
internal DB-integrity test runner."""

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
