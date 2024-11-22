#!/usr/bin/env python3

"""GUI to add corrections.tsv to the database and give feedback."""

import csv
import PySimpleGUI as sg # type: ignore

from rich import print

from tools.goldendict_tools import open_in_goldendict
from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.meaning_construction import make_meaning_combo
from tools.meaning_construction import summarize_construction
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict


class ProgData():
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.corrections_list = load_corrections_tsv(self.pth)
        self.headword: DpdHeadword = DpdHeadword()
        self.index: int

def main():
    window = make_window()
    g = ProgData()

    while True:
        event, values = window.read()
        print(event)
        print(values)

        if event == sg.WIN_CLOSED:
            break

        if event == "id_enter":
            id_val = values["id"]
            headword = g.db_session \
                .query(DpdHeadword) \
                .filter(DpdHeadword.id == id_val) \
                .first()
            if headword:
                g.headword = headword
                summary = make_summary(g)
                window["id_info"].update(value=summary)
            else:
                sg.popup_error(f"No entry with id {id_val}")

        elif event == "field1":
            val = getattr(g.headword, values["field1"])
            window["value1_old"].update(val)
            window["value1_new"].update(val)

            if values["field1"] == "source_1":
                print("!")
                window["field2"].update(value="sutta_1")
                window["value2_old"].update(
                    getattr(g.headword, "sutta_1"))
                window["field3"].update(value="example_1")
                window["value3_old"].update(
                    getattr(g.headword, "example_1"))

            if values["field1"] == "source_2":
                print("!")
                window["field2"].update(value="sutta_2")
                window["value2_old"].update(
                    getattr(g.headword, "sutta_2"))
                window["field3"].update(value="example_2")
                window["value3_old"].update(
                    getattr(g.headword, "example_2"))

        elif event == "field2":
            window["value2_old"].update(
                getattr(g.headword, values["field2"]))
            window["value2_new"].update(
                getattr(g.headword, values["field2"]))

        elif event == "field3":
            window["value3_old"].update(
                getattr(g.headword, values["field3"]))
            window["value3_new"].update(
                getattr(g.headword, values["field3"]))

        elif event == "clear_all":
            clear_all(values, window)

        elif event == "submit":
            save_corrections_tsv(values, g)
            clear_all(values, window)

        elif event.startswith("clear") and event[5:].isdigit():
            win_index = event.lstrip("clear")
            window["field" + win_index].reset()
            for value in values:
                if win_index in value:
                    window[value].update(value="")

        elif event.endswith("_key") and event.startswith("field"):
            combo = window[event.rstrip("_key")]
            combo.filter()

        elif event.endswith("_enter") and event.startswith("field"):
            combo = window[event.rstrip("_enter")]
            combo.complete()

        elif event.endswith("_focus-out") and event.startswith("field"):
            combo = window[event.rstrip("_focus-out")]
            combo.hide_tooltip()

        if event == "start":
            find_next_correction(g, window, values)
            values["add_approved"] = ""

        elif event == "approve_button":
            write_to_db(g, values)
            values["add_approved"] = "yes"
            update_corrections_tsv(g, values)
            clear_all_add_tab(values, window)
            find_next_correction(g, window, values)

        elif event == "reject_button":
            if values["add_feedback"]:
                values["add_approved"] = "no"
                update_corrections_tsv(g, values)
                clear_all_add_tab(values, window)
                find_next_correction(g, window, values)
            else:
                sg.popup(
                    "Warning!", "Can't reject without feedback!",
                    title="No Feedback!")

        elif event == "pass_button":
            values["add_approved"] = ""
            clear_all_add_tab(values, window)
            find_next_correction(g, window, values)

    window.close()


def make_window():
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

    add_corrections_tab = [
        [
            sg.Text("remaining", size=(15, 1)),
            sg.Text("", key="remaining"),
        ],
        [
            sg.Text("id", size=(15, 1)),
            sg.Input("", key="add_id", size=(20, 1)),
            sg.Button(
                "Start", key="start", font=(None, 13)),
        ],
        [
            sg.Text("summary", size=(15, 1)),
            sg.Multiline(
                "", key="add_summary", size=(50, 1), disabled=True,
                pad=((0, 100), (0, 0)))
        ],
        [
            sg.Text("field1", size=(15, 1)),
            sg.Input(
                key="add_field1", size=(50, 1), text_color="#00bfff",
                enable_events=True)
        ],
        [
            sg.Text("value1_new", size=(15, 1)),
            sg.Multiline(
                "", key="add_value1_new", size=(50, 4),
                enable_events=True),
            sg.Text("old", size=(5, 1), justification="right"),
            sg.Multiline(
                "", key="add_value1_old", size=(50, 4), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("field2", size=(15, 1)),
            sg.Input(
                key="add_field2", size=(50, 1), text_color="#00bfff",
                enable_events=True)
        ],
        [
            sg.Text("value2_new", size=(15, 1)),
            sg.Multiline(
                key="add_value2_new", size=(50, 4),
                enable_events=True),
            sg.Text("old", size=(5, 1), justification="right"),
            sg.Multiline(
                "", key="add_value2_old", size=(50, 4), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("field3", size=(15, 1)),
            sg.Input(
                key="add_field3", size=(50, 1), text_color="#00bfff",
                enable_events=True),
        ],
        [
            sg.Text("value3_new", size=(15, 1)),
            sg.Multiline(
                key="add_value3_new", size=(50, 4), enable_events=True),
            sg.Text("old", size=(5, 1), justification="right"),
            sg.Multiline(
                key="add_value3_old", size=(50, 4), disabled=True,
                background_color="black"),
        ],
        [
            sg.Text("comment", size=(15, 1)),
            sg.Input(
                "", key="add_comment", size=(50, 1), enable_events=True),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("feedback", size=(15, 1)),
            sg.Input(
                "", key="add_feedback", size=(50, 1), enable_events=True),
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


def make_summary(g: ProgData):
    word = g.headword.lemma_1
    pos = g.headword.pos
    meaning = make_meaning_combo(g.headword)
    construction = summarize_construction(g.headword)
    return f"{word}: {pos}. {meaning} [{construction}]"


def save_corrections_tsv(values, g: ProgData):
    headings = [
        "id",
        "field1", "value1_new",
        "field2", "value2_new",
        "field3", "value3_new",
        "comment", "feedback", "approved"
    ]

    if not g.pth.corrections_tsv_path.exists():
        with open(g.pth.corrections_tsv_path, "w", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(headings)

    with open(g.pth.corrections_tsv_path, "a") as file:
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


def find_next_correction(g: ProgData, window, values):
    for index, correction in enumerate(g.corrections_list):
        if (
            (correction.field1 and not correction.approved)
            or (correction.field2 and not correction.approved)
            or (correction.field3 and not correction.approved)
        ):
            print(correction)
            load_next_correction(g, correction, window)
            open_in_goldendict(correction.id)
            g.index = index
            break


def load_next_correction(g: ProgData, correction, window):
    headword = g.db_session \
        .query(DpdHeadword) \
        .filter(correction.id == DpdHeadword.id) \
        .first()
    if headword:
        g.headword = headword
        window["remaining"].update(get_remaining_corrections(g))
        window["add_id"].update(correction.id)
        window["add_summary"].update(make_summary(g))
        # field1
        if correction.field1:
            window["add_field1"].update(correction.field1)
            window["add_value1_old"].update(getattr(headword, correction.field1))
            window["add_value1_new"].update(correction.value1)
        # field2
        if correction.field2:
            window["add_field2"].update(correction.field2)
            window["add_value2_old"].update(getattr(headword, correction.field2))
            window["add_value2_new"].update(correction.value2)
        # field3
        if correction.field3:
            window["add_field3"].update(correction.field3)
            window["add_value3_old"].update(getattr(headword, correction.field3))
            window["add_value3_new"].update(correction.value3)
        window["add_comment"].update(correction.comment)
    else:
        message = f"{correction.id} not found"
        window["add_summary"].update(message, text_color="red")


def write_to_db(g: ProgData, values):
    if g.headword:
        field1 = values["add_field1"]
        field2 = values["add_field2"]
        field3 = values["add_field3"]
        value1 = values["add_value1_new"]
        value2 = values["add_value2_new"]
        value3 = values["add_value3_new"]

        if field1:
            setattr(g.headword, field1, value1)
            print(f'{g.headword.id} {g.headword.lemma_1} [yellow]{field1} [white]updated to [yellow]{value1}')
        if field2:
            setattr(g.headword, field2, value2)
            print(f'{g.headword.id} {g.headword.lemma_1} [yellow]{field2} [white]updated to [yellow]{value2}')
        if field3:
            setattr(g.headword, field3, value3)
            print(f'{g.headword.id} {g.headword.lemma_1} [yellow]{field3} [white]updated to [yellow]{value3}')
        g.db_session.commit()


def update_corrections_tsv(g: ProgData, values):
    fields = [
        "add_id",
        "add_field1", "add_value1_new",
        "add_field2", "add_value2_new",
        "add_field3", "add_value3_new",
        "add_comment", "add_feedback", "add_approved"
    ]

    correction = g.corrections_list[g.index]
    for field in fields:
        new_field = field.replace("add_", "").replace("_new", "")
        print(field, new_field)
        setattr(correction, new_field, values[field])
        print(new_field, getattr(correction, new_field))

    file_path = g.pth.corrections_tsv_path
    write_tsv_dot_dict(file_path, g.corrections_list)


def get_remaining_corrections(g):
    return len([x for x in g.corrections_list if x.approved == ""])


if __name__ == "__main__":
    main()

    # pth = ProjectPaths()
    # corrections = load_corrections_tsv(pth)
    # print(corrections)
