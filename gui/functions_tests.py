""""Functions related to running database tests using GUI.
Types of tests:
1. individual internal tests - runs in edit tab
2. db internal tests - runs in test tab
"""

import re
import csv
import subprocess
import pyperclip

from json import dumps, loads
from typing import List, Tuple
from rich import print

from tools.paths import ProjectPaths as PTH
from db.get_db_session import get_db_session
from db.models import PaliWord
from tests.helpers import InternalTestRow
from tools.pali_sort_key import pali_sort_key

# 1. individual internal tests


def open_internal_tests():
    subprocess.Popen(
        ["libreoffice", PTH.internal_tests_path])


def individual_internal_tests(
        sg, window, values, flags, primary_user):
    flags.tested = False
    internal_tests_list = make_internal_tests_list()
    test_the_tests(internal_tests_list, window)
    flags = run_individual_internal_tests(
        internal_tests_list, values, window, flags, sg, primary_user)
    return flags


def make_internal_tests_list():
    with open(PTH.internal_tests_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        internal_tests_list = [InternalTestRow(**row) for row in reader]
    return internal_tests_list


def write_internal_tests_list(internal_tests_list):
    with open(PTH.internal_tests_path, 'w', newline="") as csvfile:
        fieldnames = internal_tests_list[0].__dict__.keys()
        writer = csv.DictWriter(csvfile, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in internal_tests_list:
            row_dict = row.__dict__
            row_dict['exceptions'] = dumps(
                list(row.exceptions), ensure_ascii=False)
            writer.writerow(row_dict)

        for row in internal_tests_list:
            row_dict = row.__dict__
            row_dict['exceptions'] = loads(row.exceptions)


def test_the_tests(internal_tests_list, window):
    column_names = [column.name for column in PaliWord.__table__.columns]
    column_names += [""]
    logical_operators = [
        "",
        "equals", "does not equal",
        "contains", "contains word",
        "does not contain", "does not contain word",
        "is empty", "is not empty"]

    for test_counter, t in enumerate(internal_tests_list):
        flag = True
        message = ""
        if t.search_column_1 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_1' '{t.search_column_1}' invalid"
            flag = False
        if t.search_column_2 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_2' '{t.search_column_2}' invalid"
            flag = False
        if t.search_column_3 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_3' '{t.search_column_3}' invalid"
            flag = False
        if t.search_column_4 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_4' '{t.search_column_4}' invalid"
            flag = False
        if t.search_column_5 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_5' '{t.search_column_5}' invalid"
            flag = False
        if t.search_column_6 not in column_names:
            message = f"{test_counter}. {t.test_name} 'search_column_6' '{t.search_column_6}' invalid"

        if flag is False:
            window["messages"].update(message, text_color="red")
            print(f"[red]{message}")
            return False

        if t.search_sign_1 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_1' '{t.search_sign_1}' invalid"
            flag = False
        if t.search_sign_2 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_2' '{t.search_sign_2}' invalid"
            flag = False
        if t.search_sign_3 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_3' '{t.search_sign_3}' invalid"
            flag = False
        if t.search_sign_4 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_4' '{t.search_sign_4}' invalid"
            flag = False
        if t.search_sign_5 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_5' '{t.search_sign_5}' invalid"
            flag = False
        if t.search_sign_6 not in logical_operators:
            message = f"{test_counter}. {t.test_name} 'search_sign_6' '{t.search_sign_6}' invalid"
            flag = False

        if flag is False:
            window["messages"].update(message, text_color="red")
            print(f"[red]{message}")
            return False

    return True


def get_search_criteria(t: InternalTestRow) -> List[Tuple]:
    return [
            (t.search_column_1, t.search_sign_1, t.search_string_1),
            (t.search_column_2, t.search_sign_2, t.search_string_2),
            (t.search_column_3, t.search_sign_3, t.search_string_3),
            (t.search_column_4, t.search_sign_4, t.search_string_4),
            (t.search_column_5, t.search_sign_5, t.search_string_5),
            (t.search_column_6, t.search_sign_6, t.search_string_6)]


def run_individual_internal_tests(
        internal_tests_list, values, window, flags, sg, primary_user):

    # remove all spaces front and back, and doublespaces
    for value in values:
        if type(values[value]) == str:
            values[value] = re.sub(" +", " ", values[value])
            values[value] = values[value].strip()
            window[value].update(values[value])

    for counter, t in enumerate(internal_tests_list):

        # try:
        if t.exceptions != {""}:
            if values["pali_1"] in t.exceptions:
                print(f"[red]{counter}. {t.exceptions}")
                continue

        search_criteria = [
            (t.search_column_1, t.search_sign_1, t.search_string_1),
            (t.search_column_2, t.search_sign_2, t.search_string_2),
            (t.search_column_3, t.search_sign_3, t.search_string_3),
            (t.search_column_4, t.search_sign_4, t.search_string_4),
            (t.search_column_5, t.search_sign_5, t.search_string_5),
            (t.search_column_6, t.search_sign_6, t.search_string_6)
            ]

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

        message = f"{counter+2}. {t.test_name}"

        if all(test_results.values()):
            if t.error_column != "":
                window[f"{t.error_column}_error"].update(
                    f"{counter+2}. {t.test_name}")

            window["messages"].update(
                f"{message} - failed!", text_color="red")

            exception_popup = sg.popup_get_text(
                f"{message}\nClick Ok to add exception or Cancel to edit.",
                default_text=values["pali_1"],
                location=(200, 200),
                text_color="white"
                )

            if exception_popup is None:
                return flags
            else:
                if primary_user:
                    internal_tests_list[counter].exceptions += [values['pali_1']]
                    write_internal_tests_list(internal_tests_list)
                else:
                    sg.popup_ok(
                        "Sorry, you don't have permission to edit that.\n\
Try to fix the problem and run Tests again.",
                        title="Error",
                        location=(400, 400))
                    return flags

        else:
            window["messages"].update(
                f"{message} - passed!", text_color="white")
            # print(f"{message} - passed!")

    else:
        window["messages"].update(
            "all tests passed!", text_color="white")
        # print("exit test")
        flags.tested = True
        return flags


def db_internal_tests_setup():

    db_session = get_db_session(PTH.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    internal_tests_list = make_internal_tests_list()

    return dpd_db, internal_tests_list


def get_db_test_results(t, values):
    search_criteria: List[Tuple] = get_search_criteria(t)

    test_results = {}

    for count, criterion in enumerate(search_criteria, start=1):

        if criterion[1] == "":
            test_results[f"test{count}"] = True
        elif criterion[1] == "equals":
            test_results[f"test{count}"] = getattr(
                values, criterion[0]) == criterion[2]
        elif criterion[1] == "does not equal":
            test_results[f"test{count}"] = getattr(
                values, criterion[0]) != criterion[2]
        elif criterion[1] == "contains":
            test_results[f"test{count}"] = re.findall(
                criterion[2], getattr(values, criterion[0])) != []
        elif criterion[1] == "does not contain":
            test_results[f"test{count}"] = re.findall(
                criterion[2], getattr(values, criterion[0])) == []
        elif criterion[1] == "contains word":
            test_results[f"test{count}"] = re.findall(
                fr"\b{criterion[2]}\b", getattr(values, criterion[0])) != []
        elif criterion[1] == "does not contain word":
            test_results[f"test{count}"] = re.findall(
                fr"\b{criterion[2]}\b", getattr(values, criterion[0])) == []
        elif criterion[1] == "is empty":
            test_results[f"test{count}"] = getattr(values, criterion[0]) == ""
        elif criterion[1] == "is not empty":
            test_results[f"test{count}"] = getattr(values, criterion[0]) != ""
        else:
            print(f"[red]search_{count} error")

    return test_results


def db_internal_tests(sg, window, flags):
    clear_tests(window)
    window["messages"].update("running tests", text_color="white")
    window.refresh()

    dpd_db, internal_tests_list = db_internal_tests_setup()
    internal_tests_list = clean_exceptions(dpd_db, internal_tests_list)
    integrity = test_the_tests(internal_tests_list, window)
    if integrity is False:
        return

    for test_counter, t in enumerate(internal_tests_list):

        window["test_number"].update(
            f"{test_counter+2}")
        window["test_name"].update(t.test_name)
        window["messages"].update(t.test_name, text_color="white")
        window.refresh()

        fail_list = []
        test_results_display = [[t.display_1, t.display_2, t.display_3]]
        results_count = 0

        for i in dpd_db:
            test_results = get_db_test_results(t, i)

            if all(test_results.values()):
                if i.pali_1 not in t.exceptions:
                    fail_list += [i.pali_1]

                    if results_count < int(t.iterations):
                        test_results_display += [[
                            f"{getattr(i, t.display_1)}",
                            f"{getattr(i, t.display_2)}",
                            f"{getattr(i, t.display_3)}"]]
                        results_count += 1

        if fail_list:
            fail_list_redux = (fail_list[:int(t.iterations)])
            add_exceptions_list = fail_list_redux
            db_query = regex_fail_list(fail_list_redux)
            window["test_name"].update(t.test_name)
            window["search_column_1"].update(t.search_column_1)
            window["search_column_2"].update(t.search_column_2)
            window["search_column_3"].update(t.search_column_3)
            window["search_column_4"].update(t.search_column_4)
            window["search_column_5"].update(t.search_column_5)
            window["search_column_6"].update(t.search_column_6)
            window["search_sign_1"].update(t.search_sign_1)
            window["search_sign_2"].update(t.search_sign_2)
            window["search_sign_3"].update(t.search_sign_3)
            window["search_sign_4"].update(t.search_sign_4)
            window["search_sign_5"].update(t.search_sign_5)
            window["search_sign_6"].update(t.search_sign_6)
            window["search_string_1"].update(t.search_string_1)
            window["search_string_2"].update(t.search_string_2)
            window["search_string_3"].update(t.search_string_3)
            window["search_string_4"].update(t.search_string_4)
            window["search_string_5"].update(t.search_string_5)
            window["search_string_6"].update(t.search_string_6)
            window["display_1"].update(t.display_1)
            window["display_2"].update(t.display_2)
            window["display_3"].update(t.display_3)
            window["error_column"].update(t.error_column)
            window["iterations"].update(t.iterations)
            window["exceptions"].update(values=t.exceptions)
            window["test_results_redux"].update(len(fail_list_redux))
            window["test_results_total"].update(len(fail_list))
            window["test_results"].update(test_results_display)
            window["test_add_exception"].update(values=add_exceptions_list)
            window["test_db_query"].update(db_query)

            while True:
                event, values = window.read()
                if event == "test_next":
                    clear_tests(window)
                    break

                if event == "test_stop":
                    window["messages"].update(
                        "testing stopped", text_color="white")
                    return

                if event == sg.WIN_CLOSED:
                    break

                if event == "test_add_exception_button":
                    exception = values["test_add_exception"]
                    internal_tests_list[test_counter].exceptions += [exception]

                    write_internal_tests_list(internal_tests_list)

                    window["messages"].update(
                        f"{exception} added to exceptions",
                        text_color="white")

                    try:
                        add_exceptions_list.remove(exception)
                        window["test_add_exception"].update(
                            values=add_exceptions_list)
                    except ValueError as e:
                        window["messages"].update(
                            f"[red]can't remove {exception} from list! {e}")

                if event == "test_delete":
                    confirmation = sg.popup_yes_no(
                        "Are you sure you want to delete this test?",
                        location=(400, 400))
                    if confirmation == "Yes":
                        del internal_tests_list[test_counter]
                        write_internal_tests_list(internal_tests_list)
                        clear_tests(window)
                        break

                if event == "test_update":
                    update_tests(internal_tests_list, test_counter, values)
                    window["messages"].update(
                        f"{test_counter}. {t.test_name} updated!",
                        text_color="white")

                if event == "test_new":
                    make_new_test(values, test_counter, internal_tests_list)
                    clear_tests(window)
                    window["messages"].update(
                        f"{values['test_name']} added to tests")
                    break

                if event == "test_db_query_copy":
                    pyperclip.copy(db_query)

                if event == "test_edit":
                    open_internal_tests()

                if event == "test_results":
                    index = values["test_results"][0]
                    pali_word = test_results_display[index][0]
                    pyperclip.copy(pali_word)

        else:
            # print(f"{test_counter}. {t.test_name} passed!")
            window["messages"].update(
                f"{test_counter}. {t.test_name} passed")

        flags.text_next = False

    window["messages"].update(
        "internal db tests complete", text_color="white")


def regex_fail_list(fail_list):
    string = "/^("
    for f in fail_list:
        string += f
        if f != fail_list[-1]:
            string += "|"
        else:
            string += ")$/"
    pyperclip.copy(string)
    return string


def update_tests(internal_tests_list, count, values):
    internal_tests_list[count].test_name = values["test_name"]
    internal_tests_list[count].search_column_1 = values["search_column_1"]
    internal_tests_list[count].search_column_2 = values["search_column_2"]
    internal_tests_list[count].search_column_3 = values["search_column_3"]
    internal_tests_list[count].search_column_4 = values["search_column_4"]
    internal_tests_list[count].search_column_5 = values["search_column_5"]
    internal_tests_list[count].search_column_6 = values["search_column_6"]

    internal_tests_list[count].search_sign_1 = values["search_sign_1"]
    internal_tests_list[count].search_sign_2 = values["search_sign_2"]
    internal_tests_list[count].search_sign_3 = values["search_sign_3"]
    internal_tests_list[count].search_sign_4 = values["search_sign_4"]
    internal_tests_list[count].search_sign_5 = values["search_sign_5"]
    internal_tests_list[count].search_sign_6 = values["search_sign_6"]

    internal_tests_list[count].search_string_1 = values["search_string_1"]
    internal_tests_list[count].search_string_2 = values["search_string_2"]
    internal_tests_list[count].search_string_3 = values["search_string_3"]
    internal_tests_list[count].search_string_4 = values["search_string_4"]
    internal_tests_list[count].search_string_5 = values["search_string_5"]
    internal_tests_list[count].search_string_6 = values["search_string_6"]

    internal_tests_list[count].error_column = values["error_column"]
    internal_tests_list[count].exceptions = values["exceptions"]
    internal_tests_list[count].iterations = values["iterations"]

    internal_tests_list[count].display_1 = values["display_1"]
    internal_tests_list[count].display_2 = values["display_2"]
    internal_tests_list[count].display_3 = values["display_3"]

    write_internal_tests_list(internal_tests_list)


def make_new_test_row(v):
    return InternalTestRow(
        test_name=v["test_name"],
        search_column_1=v["search_column_1"],
        search_sign_1=v["search_sign_1"],
        search_string_1=v["search_string_1"],
        search_column_2=v["search_column_2"],
        search_sign_2=v["search_sign_2"],
        search_string_2=v["search_string_2"],
        search_column_3=v["search_column_3"],
        search_sign_3=v["search_sign_3"],
        search_string_3=v["search_string_3"],
        search_column_4=v["search_column_4"],
        search_sign_4=v["search_sign_4"],
        search_string_4=v["search_string_4"],
        search_column_5=v["search_column_5"],
        search_sign_5=v["search_sign_5"],
        search_string_5=v["search_string_5"],
        search_column_6=v["search_column_6"],
        search_sign_6=v["search_sign_6"],
        search_string_6=v["search_string_6"],
        error_column=v["error_column"],
        display_1=v["display_1"],
        display_2=v["display_2"],
        display_3=v["display_3"],
        exceptions=[],
        iterations=v["iterations"]
    )


def make_new_test(values, test_counter, internal_tests_list):
    new_test_row = make_new_test_row(values)
    internal_tests_list.insert(test_counter + 1, new_test_row)
    write_internal_tests_list(internal_tests_list)


def clear_tests(window):
    test_fields = [
        "test_name",
        "search_column_1", "search_column_2", "search_column_3",
        "search_column_4", "search_column_5", "search_column_6",
        "search_sign_1", "search_sign_2", "search_sign_3",
        "search_sign_4", "search_sign_5", "search_sign_6",
        "search_string_1", "search_string_2", "search_string_3",
        "search_string_4", "search_string_5", "search_string_6",
        "display_1", "display_2", "display_3",
        "error_column",
        "iterations", "exceptions",
        "test_results_redux", "test_results_total",
        "test_results", "test_add_exception", "test_db_query"]

    for test_field in test_fields:
        window[test_field].update("")
    window.refresh()


def clean_exceptions(dpd_db, internal_tests_list):
    """Remove exceptions which are not headwords and
    sort exceptions in pali alphabetical order."""

    all_headwords: set = set([i.pali_1 for i in dpd_db])

    for t in internal_tests_list:
        exceptions = t.exceptions
        for exception in exceptions:
            if exception not in all_headwords:
                exceptions.remove(exception)
        exceptions_sorted = sorted(exceptions, key=pali_sort_key)
        if exceptions != exceptions_sorted:
            print(exceptions)
            print(exceptions_sorted)
            print()
        t.exceptions = exceptions_sorted

    return internal_tests_list

    # write_internal_tests_list(internal_tests_list)


# clean_exceptions()
