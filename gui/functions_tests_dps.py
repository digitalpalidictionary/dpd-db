""""Functions related to running database tests using GUI (DPS).
Types of tests:
1. individual internal tests
2. db internal tests
"""

import re
import csv
import subprocess
import pyperclip

from json import dumps, loads
from typing import List, Tuple
from rich import print

from db.models import DpdHeadword
from db_tests.helpers import InternalTestRow

from sqlalchemy.orm import joinedload

from gui.functions_tests import get_search_criteria
from gui.functions_tests import regex_fail_list
from gui.functions_tests import make_new_test
from gui.functions_tests import clean_exceptions
from gui.functions_tests import open_internal_tests

# 1. individual internal tests run in dps edit tab


def dps_open_internal_tests(dpspth):
    subprocess.Popen(
        ["libreoffice", dpspth.dps_internal_tests_path])


def dps_individual_internal_tests(
        dpspth, sg, window, values, flags_dps):
    
    flags_dps.tested = False
    individual_internal_tests_list = make_individual_internal_tests_list(dpspth)
    test_the_tests(individual_internal_tests_list, window)
    flags_dps = run_individual_internal_tests(
        dpspth, individual_internal_tests_list, values, window, flags_dps, sg)
    return flags_dps


def read_from_tsv(file_path):
    """Reads rows from a TSV file and returns a list of dictionaries."""
    with open(file_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        rows = [row for row in reader]

        if reader.fieldnames is None:
            raise ValueError("Fieldnames could not be determined from the TSV.")

    return rows


def save_to_tsv(words_list, file_name):
    with open(file_name, 'w', encoding='utf-8') as tsvfile:
        for word in words_list:
            tsvfile.write(f"{word}\n")


def replace_values_in_rows(rows):
    """Replaces specified values in a list of rows."""
    replacements = {
        'family_set': 'dps_family_set',
        'grammar': 'dps_grammar',
        'pos': 'dps_pos',
        'suffix': 'dps_suffix',
        'verb': 'dps_verb',
        'meaning_lit': 'dps_meaning_lit',
        'meaning_1': 'dps_meaning_1',
        'notes': 'dps_notes',
        'ru.ru_meaning': 'dps_ru_meaning',
        'ru.ru_meaning_lit': 'dps_ru_meaning_lit',
        'sbs.sbs_meaning': 'dps_sbs_meaning',
        'ru.ru_notes': 'dps_ru_notes',
        'sbs.sbs_example_1': 'dps_sbs_example_1',
        'sbs.sbs_example_2': 'dps_sbs_example_2',
        'sbs.sbs_example_3': 'dps_sbs_example_3',
        'sbs.sbs_example_4': 'dps_sbs_example_4',
        'sbs.sbs_source_1' : 'dps_sbs_source_1',
        'sbs.sbs_source_2' : 'dps_sbs_source_2',
        'sbs.sbs_source_3' : 'dps_sbs_source_3',
        'sbs.sbs_source_4' : 'dps_sbs_source_4',
        'sbs.sbs_sutta_1' : 'dps_sbs_sutta_1',
        'sbs.sbs_sutta_2' : 'dps_sbs_sutta_2',
        'sbs.sbs_sutta_3' : 'dps_sbs_sutta_3',
        'sbs.sbs_sutta_4' : 'dps_sbs_sutta_4',
    }
    
    modified_rows = []
    for row in rows:
        modified_row = {key: replacements.get(value, value) for key, value in row.items()}
        modified_rows.append(modified_row)

    return modified_rows


def make_db_internal_tests_list(dpspth):
    """Constructs a list of InternalTestRow objects from the TSV."""
    rows = read_from_tsv(dpspth.dps_internal_tests_path)
    return [InternalTestRow(**row) for row in rows]


def make_dpd_db_internal_tests_list(pth):
    """Constructs a list of InternalTestRow objects from the TSV."""
    rows = read_from_tsv(pth.internal_tests_path)
    return [InternalTestRow(**row) for row in rows]


def make_individual_internal_tests_list(dpspth):
    """Replaces values in the rows and constructs a list of InternalTestRow objects."""
    rows = read_from_tsv(dpspth.dps_internal_tests_path)
    modified_rows = replace_values_in_rows(rows)
    return [InternalTestRow(**modified_row) for modified_row in modified_rows]


def write_exceptions_to_internal_tests_list(dpspth, internal_tests_list):
    # Read the current contents of the file
    with open(dpspth.dps_internal_tests_path, 'r', newline="") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        current_data = [row for row in reader]

    # Map test list to a dictionary for easy look-up
    tests_map = {test.test_name: test for test in internal_tests_list}

    # Update 'exceptions' column based on the new data from the internal_tests_list
    for row in current_data:
        test = tests_map.get(row['test_name'])
        if test:
            row['exceptions'] = dumps(list(test.exceptions), ensure_ascii=False)

    # Write the updated rows back to the same file
    with open(dpspth.dps_internal_tests_path, 'w', newline="") as csvfile:
        if current_data:
            fieldnames = current_data[0].keys()
        else:
            fieldnames = internal_tests_list[0].__dict__.keys()

        writer = csv.DictWriter(csvfile, delimiter="\t", fieldnames=fieldnames)
        writer.writeheader()
        for row in current_data:
            writer.writerow(row)


def write_internal_tests_list(dpspth, internal_tests_list):


    with open(dpspth.dps_internal_tests_path, 'w', newline="") as csvfile:
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



def is_valid_column(column_name):
    """Check if the given column_name is a valid attribute or relationship.attribute"""

    if not column_name:  # if column_name is empty, consider it valid
        return True

    if "." in column_name:  # Check for nested attributes
        relationship_name, attr_name = column_name.split(".", 1)
        if hasattr(DpdHeadword, relationship_name):
            related_class = getattr(DpdHeadword, relationship_name).property.mapper.class_
            return hasattr(related_class, attr_name)
    else:  # Direct attribute
        return column_name in [column.name for column in DpdHeadword.__table__.columns]
    return False



def get_nested_attr(obj, attr_str, default=None):
    """
    Get a nested attribute of an object, or return a default value if any attribute in the chain doesn't exist.
    """
    attributes = attr_str.split('.')
    for attr in attributes:
        if not hasattr(obj, attr):
            return default  # Return default value if an attribute doesn't exist
        obj = getattr(obj, attr)
    return obj



def test_the_tests(internal_tests_list, window):

    # Extract column names
    column_names = [column.name for column in DpdHeadword.__table__.columns]
    column_names += [""]

    # Define logical operators
    logical_operators = [
        "",
        "equals", "does not equal",
        "contains", "contains word",
        "does not contain", "does not contain word",
        "is empty", "is not empty"]

    # Track errors
    errors = []

    for test_counter, t in enumerate(internal_tests_list):

        # Check columns
        for i in range(1, 7):  # assuming you have up to search_column_6
            column = get_nested_attr(t, f"search_column_{i}")
            if not is_valid_column(column):
                if not column:
                    message = f"{test_counter}. {t.test_name} 'search_column_{i}' is empty. If this is intended, please adjust the validation or TSV file."
                else:
                    message = f"{test_counter}. {t.test_name} 'search_column_{i}' '{column}' invalid"
                errors.append(message)

        # Check logical operators
        for i in range(1, 7):  # assuming you have up to search_sign_6
            sign = get_nested_attr(t, f"search_sign_{i}")
            if sign not in logical_operators:
                message = f"{test_counter}. {t.test_name} 'search_sign_{i}' '{sign}' invalid"
                errors.append(message)

        # Display errors
        for error in errors:
            window["messages"].update(error, text_color="red")
            print(f"[red]{error}")

        return len(errors) == 0  # True if no errors, otherwise False



def run_individual_internal_tests(
        dpspth, internal_tests_list, values, window, flags_dps, sg):

    # remove all spaces front and back, and doublespaces
    for value in values:
        if isinstance(values[value], str):
            values[value] = re.sub(" +", " ", values[value])
            values[value] = values[value].strip()
            window[value].update(values[value])

    for counter, t in enumerate(internal_tests_list):

        # try:
        if t.exceptions != {""}:
            if values["dps_lemma_1"] in t.exceptions:
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

        try:
            for x, criterion in enumerate(search_criteria, start=1):
                if not criterion[1]:
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
        except Exception as e:
            window["messages"].update(
                f"{e}", text_color="red")
            return flags_dps

        message = f"{counter+2}. {t.test_name}"

        if all(test_results.values()):
            if t.error_column:
                window[f"{t.error_column}_error"].update(
                    f"{counter+2}. {t.test_name}")

            window["messages"].update(
                f"{message} - failed!", text_color="red")

            exception_popup = sg.popup_get_text(
                f"{message}\nClick Ok to add exception or Cancel to edit.",
                default_text=values["dps_lemma_1"],
                location=(200, 200),
                text_color="white"
                )

            if exception_popup is None:
                return flags_dps
            else:
                internal_tests_list[counter].exceptions += [values['dps_lemma_1']]
                write_exceptions_to_internal_tests_list(dpspth, internal_tests_list)
                return flags_dps

        else:
            window["messages"].update(
                f"{message} - passed!", text_color="white")
            # print(f"{message} - passed!")

    else:
        window["messages"].update(
            "all tests passed!", text_color="SpringGreen")
        # print("exit test")
        flags_dps.tested = True
        return flags_dps


# 2. db internal tests - runs in dps test tab


def get_db_test_results(t, values):

    search_criteria: List[Tuple] = get_search_criteria(t)

    test_results = {}

    for count, criterion in enumerate(search_criteria, start=1):

        if not criterion[0]:  # checking if it's an empty string
            continue

        actual_value = get_nested_attr(values, criterion[0])

        if actual_value is not None:

            if not criterion[1]:
                test_results[f"test{count}"] = True
            elif criterion[1] == "equals":
                test_results[f"test{count}"] = actual_value == criterion[2]
            elif criterion[1] == "does not equal":
                test_results[f"test{count}"] = actual_value != criterion[2]
            elif criterion[1] == "contains":
                test_results[f"test{count}"] = re.findall(
                    criterion[2], actual_value) != []
            elif criterion[1] == "does not contain":
                test_results[f"test{count}"] = re.findall(
                    criterion[2], actual_value) == []
            elif criterion[1] == "contains word":
                test_results[f"test{count}"] = re.findall(
                    fr"\b{criterion[2]}\b", actual_value) != []
            elif criterion[1] == "does not contain word":
                test_results[f"test{count}"] = re.findall(
                    fr"\b{criterion[2]}\b", actual_value) == []
            elif criterion[1] == "is empty":
                test_results[f"test{count}"] = actual_value == ""
            elif criterion[1] == "is not empty":
                test_results[f"test{count}"] = actual_value != ""
            else:
                print(f"[red]search_{count} error")
        else:
            print(f"Attribute {criterion[0]} does not exist.")

    return test_results


def dps_db_internal_tests(dpspth, pth, db_session, sg, window, flags_dps):
    clear_tests(window)
    window["messages"].update("running tests", text_color="white")
    window.refresh()

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()
    db_internal_tests_list = make_db_internal_tests_list(dpspth)

    db_internal_tests_list = clean_exceptions(dpd_db, db_internal_tests_list)
    integrity = test_the_tests(db_internal_tests_list, window)
    if not integrity:
        return

    for test_counter, t in enumerate(db_internal_tests_list):

        window["dps_test_number"].update(f"{test_counter+2}")
        window["dps_test_name"].update(t.test_name)
        window["messages"].update(t.test_name, text_color="white")
        window.refresh()

        fail_list = []
        test_results_display = [[t.display_1, t.display_2, t.display_3]]
        results_count = 0

        for i in dpd_db:
            # Check for the existence of "ru" before running the tests
            if not get_nested_attr(i, 'ru.ru_meaning'):
                    continue  # skip this iteration if ru.ru_meaning does not exist or is empty


            test_results = get_db_test_results(t, i)

            if all(test_results.values()):
                if i.lemma_1 not in t.exceptions:
                    fail_list += [i.lemma_1]

                    if results_count < int(t.iterations):
                        if not t.display_1:  # checking if it's an empty string
                            continue
                        test_results_display += [[
                            f"{get_nested_attr(i, t.display_1)}",
                            f"{get_nested_attr(i, t.display_2)}",
                            f"{get_nested_attr(i, t.display_3)}"]]
                        results_count += 1

        if fail_list:
            fail_list_redux = (fail_list[:int(t.iterations)])
            add_exceptions_list = fail_list_redux
            db_query = regex_fail_list(fail_list_redux)
            window["dps_test_name"].update(t.test_name)
            window["dps_test_search_column_1"].update(t.search_column_1)
            window["dps_test_search_column_2"].update(t.search_column_2)
            window["dps_test_search_column_3"].update(t.search_column_3)
            window["dps_test_search_column_4"].update(t.search_column_4)
            window["dps_test_search_column_5"].update(t.search_column_5)
            window["dps_test_search_column_6"].update(t.search_column_6)
            window["dps_test_search_sign_1"].update(t.search_sign_1)
            window["dps_test_search_sign_2"].update(t.search_sign_2)
            window["dps_test_search_sign_3"].update(t.search_sign_3)
            window["dps_test_search_sign_4"].update(t.search_sign_4)
            window["dps_test_search_sign_5"].update(t.search_sign_5)
            window["dps_test_search_sign_6"].update(t.search_sign_6)
            window["dps_test_search_string_1"].update(t.search_string_1)
            window["dps_test_search_string_2"].update(t.search_string_2)
            window["dps_test_search_string_3"].update(t.search_string_3)
            window["dps_test_search_string_4"].update(t.search_string_4)
            window["dps_test_search_string_5"].update(t.search_string_5)
            window["dps_test_search_string_6"].update(t.search_string_6)
            window["dps_test_display_1"].update(t.display_1)
            window["dps_test_display_2"].update(t.display_2)
            window["dps_test_display_3"].update(t.display_3)
            window["dps_test_error_column"].update(t.error_column)
            window["dps_test_iterations"].update(t.iterations)
            window["dps_test_exceptions"].update(values=t.exceptions)
            window["dps_test_results_redux"].update(len(fail_list_redux))
            window["dps_test_results_total"].update(len(fail_list))
            window["dps_test_results"].update(test_results_display)
            window["dps_test_add_exception"].update(values=add_exceptions_list)
            window["dps_test_db_query"].update(db_query)

            while True:
                event, values = window.read()
                if event == "dps_test_next":
                    clear_tests(window)
                    break

                if event == "dps_test_stop":
                    window["messages"].update(
                        "testing stopped", text_color="white")
                    return

                if event == sg.WIN_CLOSED:
                    break

                if event == "dps_test_add_exception_button":
                    exception = values["dps_test_add_exception"]
                    db_internal_tests_list[test_counter].exceptions += [exception]

                    write_internal_tests_list(dpspth, db_internal_tests_list)

                    window["messages"].update(
                        f"{exception} added to exceptions",
                        text_color="white")

                    try:
                        add_exceptions_list.remove(exception)
                        window["dps_test_add_exception"].update(
                            values=add_exceptions_list)
                    except ValueError as e:
                        window["messages"].update(
                            f"[red]can't remove {exception} from list! {e}")

                if event == "dps_test_delete":
                    confirmation = sg.popup_yes_no(
                        "Are you sure you want to delete this test?",
                        location=(400, 400))
                    if confirmation == "Yes":
                        del db_internal_tests_list[test_counter]
                        write_internal_tests_list(dpspth, db_internal_tests_list)
                        clear_tests(window)
                        break

                if event == "dps_test_update":
                    update_tests(dpspth, db_internal_tests_list, test_counter, values)
                    window["messages"].update(
                        f"{test_counter}. {t.test_name} updated!",
                        text_color="white")

                if event == "dps_test_new":
                    make_new_test(pth, values, test_counter, db_internal_tests_list)
                    clear_tests(window)
                    window["messages"].update(
                        f"{values['dps_test_name']} added to tests")
                    break

                if event == "dps_test_db_query_copy":
                    pyperclip.copy(db_query)

                if event == "dps_test_save_list":
                    print(f"words, saved to tsv: {fail_list_redux}")
                    try:
                        save_to_tsv(fail_list_redux, dpspth.dps_test_1_path)
                    except ValueError:
                    # The content is not a number, so we skip it
                        continue

                if event == "dps_test_edit":
                    dps_open_internal_tests(dpspth)

                if event == "dps_test_results":
                    if values["dps_test_results"]:
                        index = values["dps_test_results"][0]
                        pali_word = test_results_display[index][0]
                        pyperclip.copy(pali_word)
                    else:
                        # Handle the scenario where the list is empty.
                        print("dps_test_results is empty!")
                        # or take some other appropriate action
                    

        else:
            # print(f"{test_counter}. {t.test_name} passed!")
            window["messages"].update(
                f"{test_counter}. {t.test_name} passed")

        flags_dps.text_next = False

    window["messages"].update(
        "internal db tests complete", text_color="white")


def update_tests(dpspth, internal_tests_list, count, values):

    internal_tests_list[count].test_name = values["dps_test_name"]
    internal_tests_list[count].search_column_1 = values["dps_test_search_column_1"]
    internal_tests_list[count].search_column_2 = values["dps_test_search_column_2"]
    internal_tests_list[count].search_column_3 = values["dps_test_search_column_3"]
    internal_tests_list[count].search_column_4 = values["dps_test_search_column_4"]
    internal_tests_list[count].search_column_5 = values["dps_test_search_column_5"]
    internal_tests_list[count].search_column_6 = values["dps_test_search_column_6"]

    internal_tests_list[count].search_sign_1 = values["dps_test_search_sign_1"]
    internal_tests_list[count].search_sign_2 = values["dps_test_search_sign_2"]
    internal_tests_list[count].search_sign_3 = values["dps_test_search_sign_3"]
    internal_tests_list[count].search_sign_4 = values["dps_test_search_sign_4"]
    internal_tests_list[count].search_sign_5 = values["dps_test_search_sign_5"]
    internal_tests_list[count].search_sign_6 = values["dps_test_search_sign_6"]

    internal_tests_list[count].search_string_1 = values["dps_test_search_string_1"]
    internal_tests_list[count].search_string_2 = values["dps_test_search_string_2"]
    internal_tests_list[count].search_string_3 = values["dps_test_search_string_3"]
    internal_tests_list[count].search_string_4 = values["dps_test_search_string_4"]
    internal_tests_list[count].search_string_5 = values["dps_test_search_string_5"]
    internal_tests_list[count].search_string_6 = values["dps_test_search_string_6"]

    internal_tests_list[count].error_column = values["dps_test_error_column"]
    internal_tests_list[count].exceptions = values["dps_test_exceptions"]
    internal_tests_list[count].iterations = values["dps_test_iterations"]

    internal_tests_list[count].display_1 = values["dps_test_display_1"]
    internal_tests_list[count].display_2 = values["dps_test_display_2"]
    internal_tests_list[count].display_3 = values["dps_test_display_3"]

    write_internal_tests_list(dpspth, internal_tests_list)


def make_new_test_row(v):

    return InternalTestRow(
        test_name=v["dps_test_name"],
        search_column_1=v["dps_test_search_column_1"],
        search_sign_1=v["dps_test_search_sign_1"],
        search_string_1=v["dps_test_search_string_1"],
        search_column_2=v["dps_test_search_column_2"],
        search_sign_2=v["dps_test_search_sign_2"],
        search_string_2=v["dps_test_search_string_2"],
        search_column_3=v["dps_test_search_column_3"],
        search_sign_3=v["dps_test_search_sign_3"],
        search_string_3=v["dps_test_search_string_3"],
        search_column_4=v["dps_test_search_column_4"],
        search_sign_4=v["dps_test_search_sign_4"],
        search_string_4=v["dps_test_search_string_4"],
        search_column_5=v["dps_test_search_column_5"],
        search_sign_5=v["dps_test_search_sign_5"],
        search_string_5=v["dps_test_search_string_5"],
        search_column_6=v["dps_test_search_column_6"],
        search_sign_6=v["dps_test_search_sign_6"],
        search_string_6=v["dps_test_search_string_6"],
        error_column=v["dps_test_error_column"],
        display_1=v["dps_test_display_1"],
        display_2=v["dps_test_display_2"],
        display_3=v["dps_test_display_3"],
        exceptions=[],
        iterations=v["dps_test_iterations"]
    )


def clear_tests(window):

    test_fields = [
        "dps_test_name",
        "dps_test_search_column_1", "dps_test_search_column_2", "dps_test_search_column_3",
        "dps_test_search_column_4", "dps_test_search_column_5", "dps_test_search_column_6",
        "dps_test_search_sign_1", "dps_test_search_sign_2", "dps_test_search_sign_3",
        "dps_test_search_sign_4", "dps_test_search_sign_5", "dps_test_search_sign_6",
        "dps_test_search_string_1", "dps_test_search_string_2", "dps_test_search_string_3",
        "dps_test_search_string_4", "dps_test_search_string_5", "dps_test_search_string_6",
        "dps_test_display_1", "dps_test_display_2", "dps_test_display_3",
        "dps_test_error_column",
        "dps_test_iterations", "dps_test_exceptions",
        "dps_test_results_redux", "dps_test_results_total",
        "dps_test_results", "dps_test_add_exception", "dps_test_db_query"]

    for test_field in test_fields:
        window[test_field].update("")
    window.refresh()


def dps_dpd_db_internal_tests(dpspth, db_session, pth, sg, window, flags):
    clear_tests(window)
    window["messages"].update("running tests", text_color="white")
    window.refresh()

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()
    db_internal_tests_list = make_dpd_db_internal_tests_list(pth)

    db_internal_tests_list = clean_exceptions(dpd_db, db_internal_tests_list)
    integrity = test_the_tests(db_internal_tests_list, window)
    if not integrity:
        return

    for test_counter, t in enumerate(db_internal_tests_list):

        window["test_number"].update(f"{test_counter+2}")
        window["test_name"].update(t.test_name)
        window["messages"].update(t.test_name, text_color="white")
        window.refresh()

        fail_list = []
        test_results_display = [[t.display_1, t.display_2, t.display_3]]
        results_count = 0

        for i in dpd_db:
            # Check for the existence of "ru" before running the tests
            if not get_nested_attr(i, 'ru.ru_meaning'):
                    continue  # skip this iteration if ru.ru_meaning does not exist or is empty


            test_results = get_db_test_results(t, i)

            if all(test_results.values()):
                if i.lemma_1 not in t.exceptions:
                    fail_list += [i.lemma_1]

                    if results_count < int(t.iterations):
                        if not t.display_1:  # checking if it's an empty string
                            continue
                        test_results_display += [[
                            f"{get_nested_attr(i, t.display_1)}",
                            f"{get_nested_attr(i, t.display_2)}",
                            f"{get_nested_attr(i, t.display_3)}"]]
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
                    db_internal_tests_list[test_counter].exceptions += [exception]

                    write_internal_tests_list(dpspth, db_internal_tests_list)

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
                        del db_internal_tests_list[test_counter]
                        write_internal_tests_list(dpspth, db_internal_tests_list)
                        clear_tests(window)
                        break

                if event == "test_update":
                    update_tests(dpspth, db_internal_tests_list, test_counter, values)
                    window["messages"].update(
                        f"{test_counter}. {t.test_name} updated!",
                        text_color="white")

                if event == "test_new":
                    make_new_test(pth, values, test_counter, db_internal_tests_list)
                    clear_tests(window)
                    window["messages"].update(
                        f"{values['test_name']} added to tests")
                    break

                if event == "test_db_query_copy":
                    pyperclip.copy(db_query)

                if event == "test_edit":
                    open_internal_tests(pth)

                if event == "test_results":
                    if values["test_results"]:
                        index = values["test_results"][0]
                        pali_word = test_results_display[index][0]
                        pyperclip.copy(pali_word)
                    else:
                        print("test_results is empty!")
                    

        else:
            # print(f"{test_counter}. {t.test_name} passed!")
            window["messages"].update(
                f"{test_counter}. {t.test_name} passed")

        flags.text_next = False

    window["messages"].update(
        "internal db tests complete", text_color="white")



def has_base_in_other_words(word, words):
    stopwords = ["в", "и", "не", "на", "с", "у", "к", "за", "по", "о", "под", "над", "от", "до"]  # You can extend this list
    word_parts = [part for part in word.split() if part not in stopwords]
    
    for other_word in words:
        other_word_parts = [part for part in other_word.split() if part not in stopwords]
        
        if word != other_word:
            for part in word_parts:
                if any(part in split_part for split_part in other_word_parts if part in split_part):
                    return True
                    
    return False


def find_synonyms(phrase):
    words = [word.strip() for word in phrase.split(";")]
    
    duplicates = []
    if len(words) > 3:
        for word in words:
            if has_base_in_other_words(word, words):
                duplicates.append(word)

    return list(set(duplicates))


def check_repetition(field, error_field, values, window):
    phrase = values[field]
    duplicates = find_synonyms(phrase)

    if duplicates:
        message = "повтор"
        print(message)
        window[error_field].update(message)

    return window
