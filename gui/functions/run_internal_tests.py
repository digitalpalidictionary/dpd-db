import csv
import re

from rich import print
from tests.helpers import InternalTestRow
from functions.get_paths import get_paths

pth = get_paths()


def run_internal_tests(sg, window, values):
    internal_tests_list = make_internal_tests_list()
    test_integirty_of_tests(internal_tests_list)
    internal_tests(internal_tests_list, values, window)


def make_internal_tests_list():
    with open(pth.internal_tests_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        internal_tests_list = [InternalTestRow(**row) for row in reader]
    return internal_tests_list


def test_integirty_of_tests(internal_tests_list):
    pass


def internal_tests(internal_tests_list, values, window):

    for counter, i in enumerate(internal_tests_list):

        # try:
        if i.exceptions != {""}:
            if values["pali_1"] in i.exceptions:
                print(f"[red]{counter}. {i.exceptions}")
                continue

        search_criteria = [
            (i.search_column_1, i.search_sign_1, i.search_string_1),
            (i.search_column_2, i.search_sign_2, i.search_string_2),
            (i.search_column_3, i.search_sign_3, i.search_string_3),
            (i.search_column_4, i.search_sign_4, i.search_string_4),
            (i.search_column_5, i.search_sign_5, i.search_string_5),
            (i.search_column_6, i.search_sign_6, i.search_string_6)]

        test_results = {}

        for x, criterion in enumerate(search_criteria, start=1):
            if criterion[1] == "":
                test_results[f"test{x}"] = True
            elif criterion[1] == "equals":
                test_results[f"test{x}"] = values[criterion[0]] == criterion[2]
            elif criterion[1] == "does not equal":
                test_results[f"test{x}"] = values[criterion[0]] != criterion[2]
            elif criterion[1] == "contains":
                test_results[f"test{x}"] = re.findall(
                    criterion[2], values[criterion[0]]) != []
            elif criterion[1] == "does not contain":
                test_results[f"test{x}"] = re.findall(
                    criterion[2], values[criterion[0]]) == []
            elif criterion[1] == "contains word":
                test_results[f"test{x}"] = re.findall(
                    fr"\b{criterion[2]}\b", values[criterion[0]]) != []
            elif criterion[1] == "does not contain word":
                test_results[f"test{x}"] = re.findall(
                    fr"\b{criterion[2]}\b", values[criterion[0]]) == []
            elif criterion[1] == "is empty":
                test_results[f"test{x}"] = values[criterion[0]] == ""
            elif criterion[1] == "is not empty":
                test_results[f"test{x}"] = values[criterion[0]] != ""
            else:
                print(f"[red]search_{x} error")

        message = f"{counter+2}. {i.test_name}"

        if all(test_results.values()):
            if i.error_column != "":
                window[f"{i.error_column}_error"].update(
                    f"{counter+2}. {i.error_message}")
            window["messages"].update(
                f"{message} - failed!", text_color="red")
            print(f"[red]{message} - failed!")
            break

        else:
            window["messages"].update(
                f"{message} - passed!", text_color="white")
            print(f"{message} - passed!")

        # except KeyError as e:
        #     window["messages"].update(e, text_color="red")

    else:
        window["messages"].update(
            "all tests passed!", text_color="white")
        print("exit test")
