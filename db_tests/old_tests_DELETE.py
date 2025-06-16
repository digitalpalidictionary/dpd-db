# -*- coding: utf-8 -*-
"""Class for internal tests."""

import json

import csv
from json import dumps, loads
from tools.paths import ProjectPaths

pth = ProjectPaths()


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
        except (json.JSONDecodeError, TypeError):
            self.exceptions = []
        self.iterations = iterations

    def __repr__(self) -> str:
        return f"InternalTestRow: {self.test_name}"


def make_internal_tests_list():
    with open(pth.internal_tests_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        internal_tests_list = [InternalTestRow(**row) for row in reader]
    return internal_tests_list


def write_internal_tests_list(internal_tests_list):
    with open(pth.internal_tests_path, "w", newline="") as csvfile:
        fieldnames = internal_tests_list[0].__dict__.keys()
        writer = csv.DictWriter(csvfile, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in internal_tests_list:
            row_dict = row.__dict__
            row_dict["exceptions"] = dumps(list(row.exceptions), ensure_ascii=False)
            writer.writerow(row_dict)

        for row in internal_tests_list:
            row_dict = row.__dict__
            row_dict["exceptions"] = loads(row.exceptions)
