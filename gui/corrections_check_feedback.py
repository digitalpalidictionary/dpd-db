#!/usr/bin/env python3

"""GUI check feedback from corrections.tsv."""

import csv
import PySimpleGUI as sg # type: ignore
import subprocess

from rich import print

from tools.goldendict_tools import open_in_goldendict
from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.meaning_construction import make_meaning_combo
from tools.meaning_construction import summarize_construction
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def open_gui_corrections():
    
    window = make_window()
    db = None
    # _set_state(window, enabled=False)

    while True:
        event, values = window.read()
        print(event)
        print(values)

        if event == sg.WIN_CLOSED:
            break

        elif event.endswith("_key") and event.startswith("field"):
            combo = window[event.rstrip("_key")]
            combo.filter()

        elif event.endswith("_enter") and event.startswith("field"):
            combo = window[event.rstrip("_enter")]
            combo.complete()

        elif event.endswith("_focus-out") and event.startswith("field"):
            combo = window[event.rstrip("_focus-out")]
            combo.hide_tooltip()

        elif (
            event == "tabgroup" and
            values["tabgroup"] == "show_feedback_tab"
        ):
            corrections_list = load_corrections_tsv()
            index = find_next_correction(
                corrections_list, window, values)
            values["add_checked"] = ""
            total_fitting_rows = calculate_total_fitting_rows(corrections_list)
            window["remaining_words_count"].update(total_fitting_rows)

        elif event == "checked_button":
            corrections_list = load_corrections_tsv()
            values["add_checked"] = "yes"
            update_corrections_tsv(values, corrections_list, index)
            clear_all_add_tab(values, window)
            index = find_next_correction(
                corrections_list, window, values)
            total_fitting_rows = calculate_total_fitting_rows(corrections_list)
            window["remaining_words_count"].update(total_fitting_rows)

        elif event == "question_button":
            if values["add_deva_comment"]:
                corrections_list = load_corrections_tsv()
                values["add_checked"] = "?"
                update_corrections_tsv(values, corrections_list, index)
                clear_all_add_tab(values, window)
                index = find_next_correction(
                    corrections_list, window, values)
                total_fitting_rows = calculate_total_fitting_rows(corrections_list)
                window["remaining_words_count"].update(total_fitting_rows)
            else:
                sg.popup(
                    "Warning!", "Please comment!",
                    title="No Feedback!")

        elif event == "clear_button":
            corrections_list = load_corrections_tsv()
            values["add_checked"] = ""
            clear_all_add_tab(values, window)
            index = find_next_correction(
                corrections_list, window, values)
        
        elif event == "open_corrections_button":
            open_corrections()

        elif event == "show_commented_button":
            corrections_list = load_corrections_tsv()
            clear_all_add_tab(values, window)
            index = find_next_commented(
                corrections_list, window, values)
            values["add_checked"] = ""
            total_commented_rows = calculate_total_commented_rows(corrections_list)
            window["remaining_words_count"].update(total_commented_rows)

        elif event == "next_commented_button":
            if sg.popup_yes_no('Did you apply that correction?', 'Really Clear??') == 'Yes':
                corrections_list = load_corrections_tsv()
                values["add_checked"] = "yes"
                values["add_deva_comment"] = ""
                update_corrections_tsv(values, corrections_list, index)
                clear_all_add_tab(values, window)
                index = find_next_commented(
                    corrections_list, window, values)
                total_commented_rows = calculate_total_commented_rows(corrections_list)
                window["remaining_words_count"].update(total_commented_rows)

        elif event == 'apply_all_suggestions_btn':
            apply_all_suggestions()

    window.close()


def make_window():
    sg.theme("DarkGrey10")
    sg.set_options(
        font=("Noto Sans", 14),
        input_text_color="darkgray",
        text_color="#00bfff",
        window_location=(0, 0),
        # window_location=(None, None),  # Default behavior
        element_padding=(0, 0),
        margins=(0, 0),
    )

    empty_tab = [
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                'Apply All Suggestions', key='apply_all_suggestions_btn', tooltip='Apply all unapproved suggestions to the database'
                )
        ]
    ]

    show_feedback_tab = [
        [
            sg.Text("id", size=(15, 1)),
            sg.Input("", key="add_id", size=(20, 1)),
            sg.Text("Left:", size=(15, 1)),
            sg.Input("", key="remaining_words_count", size=(30, 1)),
        ],
        [
            sg.Text("summary", size=(15, 1)),
            sg.Multiline(
                "", key="add_summary", size=(50, 1), disabled=True,
                pad=((0, 100), (0, 0)))
        ],
        [
            sg.Text("field1", size=(15, 1)),
            sg.Input(key="add_field1", size=(50, 1), text_color="#00bfff")
        ],
        [
            sg.Text("value1_old", size=(15, 1)),
            sg.Multiline(
                "", key="add_value1_old", size=(50, 2), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("value1_new", size=(15, 1)),
            sg.Multiline(
                "", key="add_value1_new", size=(50, 2))
        ],
        [
            sg.Text("field2", size=(15, 1)),
            sg.Input(key="add_field2", size=(50, 1), text_color="#00bfff")
        ],
        [
            sg.Text("value2_old", size=(15, 1)),
            sg.Multiline(
                "", key="add_value2_old", size=(50, 2), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("value2_new", size=(15, 1)),
            sg.Multiline(
                key="add_value2_new", size=(50, 2))
        ],
        [
            sg.Text("field3", size=(15, 1)),
            sg.Input(key="add_field3", size=(50, 1), text_color="#00bfff"),
        ],
        [
            sg.Text("value3_old", size=(15, 1)),
            sg.Multiline(
                key="add_value3_old", size=(50, 4), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("value3_new", size=(15, 1)),
            sg.Multiline(
                key="add_value3_new", size=(50, 4))
        ],
        [
            sg.Text("comment", size=(15, 1)),
            sg.Input(
                "", key="add_comment", size=(50, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("feedback", size=(15, 1)),
            sg.Input(
                "", key="add_feedback", size=(50, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("deva_comment", size=(15, 1)),
            sg.Input(
                "", key="add_deva_comment", size=(50, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Comment", key="question_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Checked", key="checked_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Clear", key="clear_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Open Corrections", key="open_corrections_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "show commented", key="show_commented_button", size=(25, 1)),
            sg.Button(
                "next commented", key="next_commented_button", size=(25, 1))
        ],
    ]

    tab_group = sg.TabGroup(
        [[
            sg.Tab(
                "apply_all", empty_tab,
                key="empty_tab"),
            sg.Tab(
                "Feedback", show_feedback_tab,
                key="show_feedback_tab"),
        ]],
        key="tabgroup",
        enable_events=True,
        size=(None, None)
    )

    layout = [
        [tab_group],
    ]

    window = sg.Window(
        "Corrections",
        layout,
        resizable=True,
        finalize=True,
    )

    return window


def open_corrections():
    subprocess.Popen(
        ["libreoffice", pth.corrections_tsv_path])


def make_summary(db):
    word = db.lemma_1
    pos = db.pos
    meaning = make_meaning_combo(db)
    construction = summarize_construction(db)
    return f"{word}: {pos}. {meaning} [{construction}]"


def save_corections_tsv(values):
    headings = [
        "checked"
    ]

    if not pth.corrections_tsv_path.exists():
        with open(pth.corrections_tsv_path, "w", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(headings)

    with open(pth.corrections_tsv_path, "a") as file:
        writer = csv.writer(file, delimiter="\t")
        new_row = [str(values.get(heading, "")) for heading in headings]
        writer.writerow(new_row)


def clear_all_add_tab(values, window):
    for value in values:
        if (
            value.startswith("add_") and
            "_tab" not in value and
            "_checked" not in value
        ):
            window[value].update("")


def load_corrections_tsv():
    file_path = pth.corrections_tsv_path
    corrections_list = read_tsv_dot_dict(file_path)
    return corrections_list


def calculate_total_fitting_rows(corrections_list):
    total_fitting_rows = sum(1 for c in corrections_list if c.approved == "no" and not c.checked)
    print(f"total number unchecked: {total_fitting_rows}")
    return total_fitting_rows


def calculate_total_commented_rows(corrections_list):
    total_commented_rows = sum(1 for c in corrections_list if c.checked == "?")
    print(f"total number commented: {total_commented_rows}")
    return total_commented_rows


def find_next_correction(corrections_list, window, values):
    for index, c in enumerate(corrections_list):
        if c.approved == "no":
            if (
                (c.field1 and not c.checked) or
                (c.field2 and not c.checked) or
                (c.field3 and not c.checked)
            ):
                print(c)
                load_next_correction(c, window, values)
                return index


def find_next_commented(corrections_list, window, values):
    for index, c in enumerate(corrections_list):
        if c.checked == "?":
            if (
                (c.field1) or
                (c.field2) or
                (c.field3)
            ):
                print(c)
                load_next_correction(c, window, values)
                return index


def load_next_correction(c, window, __values__):
    db = db_session.query(DpdHeadword).filter(
        c.id == DpdHeadword.id).first()
    open_in_goldendict(c.id)
    window["add_id"].update(c.id)
    window["add_summary"].update(make_summary(db))
    # field1
    if c.field1:
        window["add_field1"].update(c.field1)
        window["add_value1_old"].update(getattr(db, c.field1))
        window["add_value1_new"].update(c.value1)
    # field2
    if c.field2:
        window["add_field2"].update(c.field2)
        window["add_value2_old"].update(getattr(db, c.field2))
        window["add_value2_new"].update(c.value2)
    # field3
    if c.field3:
        window["add_field3"].update(c.field3)
        window["add_value3_old"].update(getattr(db, c.field3))
        window["add_value3_new"].update(c.value3)
    window["add_comment"].update(c.comment)
    window["add_feedback"].update(c.feedback)
    window["add_deva_comment"].update(c.deva_comment)


def update_corrections_tsv(values, corrections_list, index):
    fields = [
        "add_checked",
        "add_deva_comment"
    ]

    c = corrections_list[index]
    for field in fields:
        new_field = field.replace("add_", "").replace("_new", "")
        print(field, new_field)
        setattr(c, new_field, values[field])
        print(new_field, getattr(c, new_field))

    file_path = pth.corrections_tsv_path
    write_tsv_dot_dict(file_path, corrections_list)


def apply_all_suggestions():

    corrections_list = load_corrections_tsv()

    added_lines_count = 0

    for correction in corrections_list:
        if not correction.approved:
            db = db_session.query(DpdHeadword).filter(
                correction.id == DpdHeadword.id).first()
            if db:
                id = correction.id
                field1 = correction.field1
                field2 = correction.field2
                field3 = correction.field3
                value1 = correction.value1
                value2 = correction.value2
                value3 = correction.value3

                if field1 and value1 is not None:
                    setattr(db, field1, value1)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field1} with {value1}")
                if field2 and value2 is not None:
                    setattr(db, field2, value2)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field2} with {value2}")
                if field3 and value3 is not None:
                    setattr(db, field3, value3)
                    added_lines_count += 1
                    print(f"{added_lines_count} {id}: {field3} with {value3}")
                
                db_session.commit()
            else:
                print(f"Entry with ID {correction.id} not found.")

    print(f"Total number of applied corrections: {added_lines_count}")


# open_gui_corrections()
apply_all_suggestions()
