#!/usr/bin/env python3

"""GUI to add corrections.tsv to the database and give feedback."""

import csv
import PySimpleGUI as sg
from sqlalchemy import inspect

from rich import print

from tools.goldedict_tools import open_in_goldendict
from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.meaning_construction import make_meaning
from tools.meaning_construction import summarize_construction
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict


ENABLE_LIST = \
    [f"field{i}" for i in range(1, 4)] + \
    [f"clear{i}" for i in range(1, 4)] + \
    ["submit", "clear_all"]


def get_column_names():
    inspector = inspect(PaliWord)
    column_names = [column.name for column in inspector.columns]
    column_names = sorted(column_names)
    return column_names


# def _set_state(window: sg.Window, enabled=True) -> None:
#     for i in ENABLE_LIST:
#         window[i].update(disabled=not enabled)


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    window = make_window()
    db = None
    # _set_state(window, enabled=False)

    while True:
        event, values = window.read()
        print(event)
        print(values)

        if event == sg.WIN_CLOSED:
            break

        if event == "id_enter":
            id_val = values["id"]
            db = db_session.query(PaliWord)\
                .filter(PaliWord.id == id_val).first()
            if db:
                summary = make_summary(db)
                window["id_info"].update(summary)
                # _set_state(window, enabled=True)
            else:
                # _set_state(window, enabled=False)
                sg.popup_error(f"No entry whith id {id_val}")

        elif event == "field1":
            val = getattr(db, values["field1"])
            window["value1_old"].update(val)
            window["value1_new"].update(val)

            if values["field1"] == "source_1":
                print("!")
                window["field2"].update("sutta_1")
                window["value2_old"].update(
                    getattr(db, "sutta_1"))
                window["field3"].update("example_1")
                window["value3_old"].update(
                    getattr(db, "example_1"))

            if values["field1"] == "source_2":
                print("!")
                window["field2"].update("sutta_2")
                window["value2_old"].update(
                    getattr(db, "sutta_2"))
                window["field3"].update("example_2")
                window["value3_old"].update(
                    getattr(db, "example_2"))

        elif event == "field2":
            window["value2_old"].update(
                getattr(db, values["field2"]))
            window["value2_new"].update(
                getattr(db, values["field2"]))

        elif event == "field3":
            window["value3_old"].update(
                getattr(db, values["field3"]))
            window["value3_new"].update(
                getattr(db, values["field3"]))

        elif event == "clear_all":
            clear_all(values, window)

        elif event == "submit":
            save_corections_tsv(values, pth)
            clear_all(values, window)

        elif event.startswith("clear") and event[5:].isdigit():
            index = event.lstrip("clear")
            window["field" + index].reset()
            for value in values:
                if index in value:
                    window[value].update("")

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
            values["tabgroup"] == "add_corrections_tab"
        ):
            corrections_list = load_corrections_tsv(pth)
            index = find_next_correction(
                db_session, corrections_list, window, values)
            values["add_approved"] = ""

        elif event == "approve_button":
            write_to_db(db_session, values)
            values["add_approved"] = "yes"
            update_corrections_tsv(pth, values, corrections_list, index)
            clear_all_add_tab(values, window)
            index = find_next_correction(
                db_session, corrections_list, window, values)

        elif event == "reject_button":
            if values["add_feedback"]:
                values["add_approved"] = "no"
                update_corrections_tsv(pth, values, corrections_list, index)
                clear_all_add_tab(values, window)
                index = find_next_correction(
                    db_session, corrections_list, window, values)
            else:
                sg.popup(
                    "Warning!", "Can't reject without feedback!",
                    title="No Feedback!")

        elif event == "pass_button":
            values["add_approved"] = ""
            clear_all_add_tab(values, window)
            index = find_next_correction(
                db_session, corrections_list, window, values)

    window.close()


def make_window():
    column_names = get_column_names()
    sg.theme("DarkGrey10")
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="darkgray",
        text_color="#00bfff",
        # window_location=(0, 0),
        window_location=(None, None),  # Default behavior
        element_padding=(0, 3),
        margins=(0, 0),
    )

    make_corrections_tab = []

    add_corrections_tab = [
        [
            sg.Text("id", size=(15, 1)),
            sg.Input("", key="add_id", size=(20, 1)),
            sg.Button(
                "Previous", key="previous", font=(None, 13)),
            sg.Button(
                "Next", key="next", font=(None, 13)),
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
            sg.Button(
                "Reject", key="reject_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Approve", key="approve_button", size=(50, 1))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Pass", key="pass_button", size=(50, 1))
        ],
    ]

    tab_group = sg.TabGroup(
        [[
            sg.Tab(
                "Make Corrections", make_corrections_tab,
                key="corrections_tab"),
            sg.Tab(
                "Add Corrections to DB", add_corrections_tab,
                key="add_corrections_tab"),
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


def make_summary(db):
    word = db.pali_1
    pos = db.pos
    meaning = make_meaning(db)
    construction = summarize_construction(db)
    return f"{word}: {pos}. {meaning} [{construction}]"


def save_corections_tsv(values, pth: ProjectPaths):
    headings = [
        "id",
        "field1", "value1_new",
        "field2", "value2_new",
        "field3", "value3_new",
        "comment", "feedback", "approved"
    ]

    if not pth.corrections_tsv_path.exists():
        with open(pth.corrections_tsv_path, "w", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(headings)

    with open(pth.corrections_tsv_path, "a") as file:
        writer = csv.writer(file, delimiter="\t")
        new_row = [str(values.get(heading, "")) for heading in headings]
        writer.writerow(new_row)


def clear_all(values, window):
    for k in ["field1", "field2", "field3"]:
        window[k].reset()
    for value in values:
        if "tab" not in value:
            window[value].update("")
            window["id_info"].update("")


def clear_all_add_tab(values, window):
    for value in values:
        if (
            value.startswith("add_") and
            "_tab" not in value and
            "_approved" not in value
        ):
            window[value].update("")


def load_corrections_tsv(pth: ProjectPaths):
    file_path = pth.corrections_tsv_path
    corrections_list = read_tsv_dot_dict(file_path)
    return corrections_list


def find_next_correction(db_session, corrections_list, window, values):
    for index, c in enumerate(corrections_list):
        if (
            (c.field1 and not c.approved) or
            (c.field2 and not c.approved) or
            (c.field3 and not c.approved)
        ):
            print(c)
            load_next_correction(db_session, c, window, values)
            return index


def load_next_correction(db_session, c, window, __values__):
    db = db_session.query(PaliWord) \
        .filter(c.id == PaliWord.id) \
        .first()
    if db:
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
    else:
        message = f"{c.id} not found"
        window["add_summary"].update(message, text_color="red")


def write_to_db(db_session, values):
    db = db_session.query(PaliWord).filter(
        values["add_id"] == PaliWord.id).first()

    field1 = values["add_field1"]
    field2 = values["add_field2"]
    field3 = values["add_field3"]
    value1 = values["add_value1_new"]
    value2 = values["add_value2_new"]
    value3 = values["add_value3_new"]

    if field1:
        setattr(db, field1, value1)
        print(f'{db.id} {db.pali_1} [yellow]{field1} \
[white]updated to [yellow]{value1}')
    if field2:
        setattr(db, field2, value2)
        print(f'{db.id} {db.pali_1} [yellow]{field2} \
[white]updated to [yellow]{value2}')
    if field3:
        setattr(db, field3, value3)
        print(f'{db.id} {db.pali_1} [yellow]{field3} \
[white]updated to [yellow]{value3}')
    db_session.commit()


def update_corrections_tsv(pth: ProjectPaths, values, corrections_list, index):
    fields = [
        "add_id",
        "add_field1", "add_value1_new",
        "add_field2", "add_value2_new",
        "add_field3", "add_value3_new",
        "add_comment", "add_feedback", "add_approved"
    ]

    c = corrections_list[index]
    for field in fields:
        new_field = field.replace("add_", "").replace("_new", "")
        print(field, new_field)
        setattr(c, new_field, values[field])
        print(new_field, getattr(c, new_field))

    file_path = pth.corrections_tsv_path
    write_tsv_dot_dict(file_path, corrections_list)


if __name__ == "__main__":
    main()
    # pth = ProjectPaths()
    # corrections = load_corrections_tsv(pth)
    # print(corrections)