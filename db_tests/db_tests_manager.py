"""Class for internal tests."""

import csv
import json
import re
from typing import NamedTuple
from pathlib import Path

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class InternalTestRow:
    def __init__(
        self,
        test_name,
        search_column_1,
        search_sign_1,
        search_string_1,
        search_column_2,
        search_sign_2,
        search_string_2,
        search_column_3,
        search_sign_3,
        search_string_3,
        search_column_4,
        search_sign_4,
        search_string_4,
        search_column_5,
        search_sign_5,
        search_string_5,
        search_column_6,
        search_sign_6,
        search_string_6,
        error_column,
        exceptions,
        iterations,
        display_1,
        display_2,
        display_3,
    ):
        self.test_name = test_name
        self.search_column_1 = search_column_1
        self.search_sign_1 = search_sign_1
        self.search_string_1 = search_string_1
        self.search_column_2 = search_column_2
        self.search_sign_2 = search_sign_2
        self.search_string_2 = search_string_2
        self.search_column_3 = search_column_3
        self.search_sign_3 = search_sign_3
        self.search_string_3 = search_string_3
        self.search_column_4 = search_column_4
        self.search_sign_4 = search_sign_4
        self.search_string_4 = search_string_4
        self.search_column_5 = search_column_5
        self.search_sign_5 = search_sign_5
        self.search_string_5 = search_string_5
        self.search_column_6 = search_column_6
        self.search_sign_6 = search_sign_6
        self.search_string_6 = search_string_6
        self.error_column = error_column
        self.display_1 = display_1
        self.display_2 = display_2
        self.display_3 = display_3

        try:
            self.exceptions = json.loads(exceptions)
        except (json.JSONDecodeError, TypeError) as e:
            pr.red(f"error loading exceptions:{test_name} {str(e)}")
            self.exceptions = []
        self.iterations = iterations

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
        self.internal_tests_list = self.load_tests()
        self.integrity_ok, self.integrity_failures = self.integrity_check()

    def load_tests(self):
        with open(self.tests_path, newline="") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="\t")
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

    def run_all_tests_on_entry(
        self, headword: DpdHeadword
    ) -> tuple[bool, list[TestFailure] | list[IntegrityFailure]]:
        """
        Run all the tests on a single headword.

        Returns `True` and empty list if is all ok.

        Returns `False` and a list of failures if not.

        """

        # dont run the test if there's an integrity failure
        if not self.integrity_ok:
            return False, self.integrity_failures

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

        return bool(error_list == []), error_list

    # def run_test_on_all_entries(self, test: InternalTestRow, db_session) -> list[bool]:
    #     dpd_db = db_session.query(DpdHeadword).all()
    #     return [self.run_test_on_entry(test, entry) for entry in dpd_db]

    # def update_test(self, test_name: str, updates: dict) -> None:
    #     for test in self.internal_tests_list:
    #         if test.test_name == test_name:
    #             for key, value in updates.items():
    #                 if hasattr(test, key):
    #                     setattr(test, key, value)
    #             break
    #     self.save_tests()

    # def save_tests(self) -> None:
    #     with open(self.tests_path, "w", newline="") as csvfile:
    #         fieldnames = self.internal_tests_list[0].__dict__.keys()
    #         writer = csv.DictWriter(csvfile, delimiter="\t", fieldnames=fieldnames)
    #         writer.writeheader()
    #         for row in self.internal_tests_list:
    #             row_dict = row.__dict__
    #             row_dict["exceptions"] = dumps(list(row.exceptions), ensure_ascii=False)
    #             writer.writerow(row_dict)


def main():
    session = get_db_session(Path("dpd.db"))

    test_manager = DbTestManager()
    entry = session.query(DpdHeadword).filter_by(id=122).first()

    if entry is not None:
        print(test_manager.run_all_tests_on_entry(entry))


if __name__ == "__main__":
    main()
