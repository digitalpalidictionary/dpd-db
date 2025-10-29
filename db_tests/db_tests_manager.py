# -*- coding: utf-8 -*-
"""Class for internal tests."""

import csv
import json
import re
from json import dumps
from pathlib import Path
from typing import NamedTuple

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class InternalTestRow:
    def __init__(
        self,
        test_name: str,
        search_column_1: str,
        search_sign_1: str,
        search_string_1: str,
        search_column_2: str,
        search_sign_2: str,
        search_string_2: str,
        search_column_3: str,
        search_sign_3: str,
        search_string_3: str,
        search_column_4: str,
        search_sign_4: str,
        search_string_4: str,
        search_column_5: str,
        search_sign_5: str,
        search_string_5: str,
        search_column_6: str,
        search_sign_6: str,
        search_string_6: str,
        error_column: str,
        exceptions: str | list[int],  # Allow string from CSV or list[int]
        iterations: str | int,  # Allow string from CSV or int
        display_1: str,
        display_2: str,
        display_3: str,
        notes: str = "",
    ) -> None:
        self.test_name: str = test_name
        self.search_column_1: str = search_column_1
        self.search_sign_1: str = search_sign_1
        self.search_string_1: str = search_string_1
        self.search_column_2: str = search_column_2
        self.search_sign_2: str = search_sign_2
        self.search_string_2: str = search_string_2
        self.search_column_3: str = search_column_3
        self.search_sign_3: str = search_sign_3
        self.search_string_3: str = search_string_3
        self.search_column_4: str = search_column_4
        self.search_sign_4: str = search_sign_4
        self.search_string_4: str = search_string_4
        self.search_column_5: str = search_column_5
        self.search_sign_5: str = search_sign_5
        self.search_string_5: str = search_string_5
        self.search_column_6: str = search_column_6
        self.search_sign_6: str = search_sign_6
        self.search_string_6: str = search_string_6
        self.error_column: str = error_column
        self.display_1: str = display_1
        self.display_2: str = display_2
        self.display_3: str = display_3
        self.notes: str = notes

        # Process exceptions
        self.exceptions: list[int] = []
        if isinstance(exceptions, str) and exceptions.strip():
            try:
                # Pass only string to json.loads
                loaded_exceptions = json.loads(exceptions)
                # Assume it's a list of ints if loading succeeds
                self.exceptions = [int(exc) for exc in loaded_exceptions]
            except (json.JSONDecodeError, ValueError) as e:
                pr.red(
                    f"Error processing exceptions for test '{test_name}': {exceptions} - {e}"
                )
                self.exceptions = []  # Default to empty on error
        elif isinstance(exceptions, list):  # Handle if already a list
            self.exceptions = [int(exc) for exc in exceptions]

        # Process iterations
        try:
            self.iterations: int = int(iterations)
        except (ValueError, TypeError) as e:
            pr.red(
                f"Invalid iterations value for test '{test_name}': {iterations} - {e}. Setting to 10."
            )
            self.iterations = 10

    def __repr__(self) -> str:
        return f"InternalTestRow: {self.test_name}"


class IntegrityFailure(NamedTuple):
    """Represents a single failure when integrity checking tests TSV."""

    test_row: int
    test_name: str
    invalid_field_name: str
    invalid_value: str


class TestFailure(NamedTuple):
    """A single test failure"""

    test_row: int
    test_name: str
    error_column: str


class DbTestManager:
    def __init__(self):
        self.pth = ProjectPaths()
        self.tests_path = self.pth.internal_tests_path
        self.fieldnames: list[str] = []
        self.internal_tests_list = self.load_tests()
        self.integrity_ok, self.integrity_failures = self.integrity_check()

    def load_tests(self):
        with open(self.tests_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
            if reader.fieldnames:
                self.fieldnames = reader.fieldnames
            internal_tests_list = [InternalTestRow(**row) for row in reader]
        return internal_tests_list

    def integrity_check(self) -> tuple[bool, list[IntegrityFailure]]:
        """
        Checks the validity of search columns and signs in the internal tests list.

        Returns `True` and an empty list if all tests are valid.

        Returns `False` and a list of TestTsvFailure named tuples for any invalid tests found.
        """

        failures: list[IntegrityFailure] = []

        column_names: list[str] = [
            column.name for column in DpdHeadword.__table__.columns
        ]
        column_names.append("")  # Add "" to allow empty values

        logical_operators: list[str] = [
            "",
            "equals",
            "does not equal",
            "contains",
            "contains word",
            "does not contain",
            "does not contain word",
            "is empty",
            "is not empty",
        ]

        for test_counter, t in enumerate(
            self.internal_tests_list,
            start=2,  # 1 for zero offset, 1 for title
        ):
            for i in range(1, 7):  # Check criteria sets 1 through 6
                # Check search_column_i
                col_attr_name = f"search_column_{i}"
                col_value = getattr(t, col_attr_name, None)
                if col_value not in column_names:
                    message = f"{test_counter}. {t.test_name} '{col_attr_name}' ('{col_value}') is invalid"
                    print(f"[red]{message}")
                    failure = IntegrityFailure(
                        test_row=test_counter,
                        test_name=t.test_name,
                        invalid_field_name=col_attr_name,
                        invalid_value=str(col_value),
                    )
                    failures.append(failure)

                # Check search_sign_i
                sign_attr_name = f"search_sign_{i}"
                sign_value = getattr(t, sign_attr_name, None)
                if sign_value not in logical_operators:
                    message = f"{test_counter}. {t.test_name} '{sign_attr_name}' ('{sign_value}') is invalid"
                    print(f"[red]{message}")
                    failure = IntegrityFailure(
                        test_row=test_counter,
                        test_name=t.test_name,
                        invalid_field_name=sign_attr_name,
                        invalid_value=str(sign_value),
                    )
                    failures.append(failure)
        if failures:
            return False, failures
        else:
            return True, failures

    @staticmethod
    def get_search_criteria(t: InternalTestRow) -> list[tuple]:
        return [
            (t.search_column_1, t.search_sign_1, t.search_string_1),
            (t.search_column_2, t.search_sign_2, t.search_string_2),
            (t.search_column_3, t.search_sign_3, t.search_string_3),
            (t.search_column_4, t.search_sign_4, t.search_string_4),
            (t.search_column_5, t.search_sign_5, t.search_string_5),
            (t.search_column_6, t.search_sign_6, t.search_string_6),
        ]

    def error_test_each_single_row(
        self,
        test: InternalTestRow,
        headword: DpdHeadword,
    ) -> bool:
        """Checks for errors on a single row.

        Returns `True` if there's an error.

        Returns `False` if there's no error.
        """

        search_criteria = self.get_search_criteria(test)
        test_results = {}

        if headword.id in test.exceptions:
            return False

        for count, criterion in enumerate(search_criteria, start=1):
            test_column, test_logic, test_string = criterion

            if not test_logic:
                test_results[f"test{count}"] = True

            elif test_logic == "equals":
                test_results[f"test{count}"] = (
                    getattr(headword, test_column) == test_string
                )
            elif test_logic == "does not equal":
                test_results[f"test{count}"] = (
                    getattr(headword, test_column) != test_string
                )
            elif test_logic == "contains":
                test_results[f"test{count}"] = (
                    re.findall(test_string, getattr(headword, test_column)) != []
                )
            elif test_logic == "does not contain":
                test_results[f"test{count}"] = (
                    re.findall(test_string, getattr(headword, test_column)) == []
                )
            elif test_logic == "contains word":
                test_results[f"test{count}"] = (
                    re.findall(rf"\b{test_string}\b", getattr(headword, test_column))
                    != []
                )
            elif test_logic == "does not contain word":
                test_results[f"test{count}"] = (
                    re.findall(rf"\b{test_string}\b", getattr(headword, test_column))
                    == []
                )
            elif test_logic == "is empty":
                test_results[f"test{count}"] = getattr(headword, test_column) == ""
            elif test_logic == "is not empty":
                test_results[f"test{count}"] = getattr(headword, test_column) != ""
            else:
                print(f"[red]search_{count} error")

        return all(test_results.values())

    def run_all_tests_on_headword(
        self, headword: DpdHeadword
    ) -> tuple[bool, list[TestFailure] | list[IntegrityFailure]]:
        """
        Run all the tests on a single headword.

        Returns `True` and empty list if is all ok.

        Returns `False` and a list of failures if not.

        """
        # Load and check integrity
        self.internal_tests_list = self.load_tests()
        integrity_ok, integrity_failures = self.integrity_check()
        if not integrity_ok:
            return False, integrity_failures

        error_list: list[TestFailure] = []
        for counter, test in enumerate(
            self.internal_tests_list,
            start=2,  # 1 for zero offset and 1 for title
        ):
            error = self.error_test_each_single_row(test, headword)
            if error:
                error_list.append(
                    TestFailure(
                        test_row=counter,
                        test_name=test.test_name,
                        error_column=test.error_column,
                    )
                )

        return not bool(error_list), error_list  # Simplified return

    def run_test_on_all_db_entries(
        self, test_definition: InternalTestRow, db: list[DpdHeadword]
    ) -> list[DpdHeadword]:
        """
        Runs a single test definition against all DpdHeadword entries in the database.
        Returns a list of DpdHeadword objects that failed the test.
        """
        failing_headwords: list[DpdHeadword] = []
        for headword in db:
            if self.error_test_each_single_row(test_definition, headword):
                failing_headwords.append(headword)
        return failing_headwords

    def save_tests(self) -> None:
        """Saves the current state of internal_tests_list back to the TSV file."""
        if not self.internal_tests_list:
            pr.red("No tests loaded, nothing to save.")
            return

        fieldnames = self.fieldnames

        try:
            with open(self.tests_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    delimiter="\t",
                    fieldnames=fieldnames,
                    quoting=csv.QUOTE_ALL,
                )
                writer.writeheader()
                for test_row in self.internal_tests_list:
                    # Create a dictionary representation for writing
                    row_dict = {}
                    for field in fieldnames:
                        # Get value, default to empty string if not present
                        value = getattr(test_row, field, "")
                        # Serialize exceptions list to JSON string
                        if field == "exceptions":
                            exceptions_list = (
                                list(value) if isinstance(value, (list, set)) else []
                            )
                            row_dict[field] = dumps(exceptions_list, ensure_ascii=False)
                        else:
                            row_dict[field] = value

                    writer.writerow(row_dict)
        except IOError as e:
            pr.red(f"Error saving tests to {self.tests_path}: {e}")
        except Exception as e:
            pr.red(f"An unexpected error occurred during saving tests: {e}")

    def add_exception(self, test_name: str, exception_id: int) -> bool:
        """Adds an exception ID to a specific test and saves the changes.

        Args:
            test_name: The name of the test to modify.
            exception_id: The ID to add to the exceptions list.

        Returns:
            True if the exception was added and saved successfully, False otherwise.
        """

        test_found = False
        for test in self.internal_tests_list:
            if test.test_name == test_name:
                test_found = True

                if exception_id not in test.exceptions:
                    test.exceptions.append(exception_id)
                    test.exceptions.sort()
                    pr.green_title(
                        f"Added exception {exception_id} to test '{test_name}'."
                    )
                    self.save_tests()
                    return True
                else:
                    # Even if it exists, consider it a success
                    return True

        if not test_found:
            pr.red(f"Test '{test_name}' not found.")
            return False

        # Fallback, should ideally not be reached
        return False

    def sort_tests_by_name(self) -> None:
        """Sorts the tests alphabetically by test_name, preserving the header row."""
        if not self.internal_tests_list:
            pr.red("No tests loaded, nothing to sort.")
            return

        # Sort the internal tests list by test_name
        self.internal_tests_list.sort(key=lambda test: test.test_name)

        # Save the sorted tests back to the TSV file
        self.save_tests()


def main() -> None:
    session = get_db_session(Path("dpd.db"))

    test_manager = DbTestManager()
    entry = session.query(DpdHeadword).filter_by(id=112).first()

    if entry is not None:
        print(test_manager.run_all_tests_on_headword(entry))


if __name__ == "__main__":
    main()
