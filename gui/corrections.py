#!/usr/bin/env python3
import csv
import PySimpleGUI as sg
from sqlalchemy import inspect

from completion_combo import CompletionCombo
from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.meaning_construction import make_meaning
from tools.meaning_construction import summarize_constr
from tools.paths import ProjectPaths as PTH


ENABLE_LIST = \
    [f"field{i}" for i in range(1, 4)] + \
    [f"clear{i}" for i in range(1, 4)] + \
    ["submit", "clear_all"]


def get_column_names():
    inspector = inspect(PaliWord)
    column_names = [column.name for column in inspector.columns]
    column_names = sorted(column_names)
    return column_names


def _set_state(window: sg.Window, enabled=True) -> None:
    for i in ENABLE_LIST:
        window[i].update(disabled=not enabled)


def main():

    db_session = get_db_session("dpd.db")
    window = make_window()
    db = None
    _set_state(window, enabled=False)

    while True:
        event, values = window.read()
        print(event, values)

        if event == sg.WIN_CLOSED:
            break

        if event == "id_enter":
            id_val = values["id"]
            db = db_session.query(PaliWord)\
                .filter(PaliWord.id == id_val).first()
            if db:
                summary = make_summary(db)
                window["id_info"].update(summary)
                _set_state(window, enabled=True)
            else:
                _set_state(window, enabled=False)
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
            save_corections_tsv(values, PTH)
            clear_all(values, window)

        elif event.startswith("clear") and event[5:].isdigit():
            index = event.lstrip("clear")
            window["field" + index].reset()
            for value in values:
                if index in value:
                    window[value].update("")

        elif event.endswith("_key") and event.startswith("field"):
            window[event.rstrip("_key")].filter()

        elif event.endswith("_enter") and event.startswith("field"):
            combo = window[event.rstrip("_enter")]
            combo.complete()

        elif event.endswith("_key_down") and event.startswith("field"):
            combo = window[event.rstrip("_key_down")]
            combo.set_tooltip(None)

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

    make_corrections_tab = [
        [
            sg.Text("id", size=(15, 1)),
            sg.Input("", key="id", size=(20, 1)),
            sg.Button(
                "Clear All", key="clear_all", font=(None, 13))
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Multiline(
                "", key="id_info", size=(100, 1), disabled=True,
                pad=((0, 100), (0, 0)))
        ],
        [
            sg.Text("field1", size=(15, 1)),
            CompletionCombo(
                column_names,
                key="field1",
                enable_events=True),
            sg.Button(
                "Clear", key="clear1", font=(None, 13))
        ],
        [
            sg.Text("value1", size=(15, 1)),
            sg.Multiline(
                "", key="value1_old", size=(50, 2), disabled=True),
            sg.Multiline(
                "", key="value1_new", size=(50, 2))
        ],
        [
            sg.Text("comment1", size=(15, 1)),
            sg.Input(
                "", key="comment1", size=(103, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("field2", size=(15, 1)),
            CompletionCombo(
                column_names,
                key="field2",
                enable_events=True),
            sg.Button("Clear", key="clear2", font=(None, 13))
        ],
        [
            sg.Text("value2", size=(15, 1)),
            sg.Multiline(
                "", key="value2_old", size=(50, 2), disabled=True),
            sg.Multiline(
                "", key="value2_new", size=(50, 2))
        ],
        [
            sg.Text("comment2", size=(15, 1)),
            sg.Input(
                "", key="comment2", size=(103, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("field3", size=(15, 1)),
            CompletionCombo(
                column_names,
                key="field3",
                enable_events=True),
            sg.Button("Clear", key="clear3", font=(None, 13)),
            sg.Text("", size=(22, 1)),
            sg.Input(key="bold", size=(30, 1)),
            sg.Button("Bold", key="bold_button", font=(None, 13)),
        ],
        [
            sg.Text("value3", size=(15, 1)),
            sg.Multiline(
                "", key="value3_old", size=(50, 4), disabled=True),
            sg.Multiline(
                "", key="value3_new", size=(50, 4))
        ],
        [
            sg.Text("comment3", size=(15, 1)),
            sg.Input(
                "", key="comment3", size=(103, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button("Submit Correction", key="submit", size=(101, 1)),
        ],
    ]

    add_corrections_tab = [
        [
            sg.Text("", size=(15, 1)),
            sg.Button("", key="approved", size=(103, 1)),
        ]
    ]

    tab_group = sg.TabGroup(
        [[
            sg.Tab(
                "Make Corrections", make_corrections_tab,
                key="corrections_tab"),
            sg.Tab(
                "Fix Corrections", add_corrections_tab,
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

    window["id"].bind("<Return>", "_enter")
    for i in range(1, 4):
        field = f"field{i}"
        window[field].bind("<Return>", "_enter")
        window[field].bind("<Key>", "_key")
        window[field].bind("<Key-Down>", "_key_down")

    return window


def make_summary(db):
    word = db.pali_1
    pos = db.pos
    meaning = make_meaning(db)
    construction = summarize_constr(db)
    return f"{word}: {pos}. {meaning} [{construction}]"


def save_corections_tsv(values, pth):
    headings = [
        "id",
        "field1", "value1_new", "comment1",
        "field2", "value2_new", "comment2",
        "field3", "value3_new", "comment3"
    ]

    if not pth.corrections_tsv_path.exists():
        with open(pth.corrections_tsv_path, "w", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow(headings)

    with open(pth.corrections_tsv_path, "a") as file:
        writer = csv.writer(file, delimiter="\t")
        new_row = [str(values[heading]) for heading in headings]
        writer.writerow(new_row)


def clear_all(values, window):
    for k in ["field1", "field2", "field3"]:
        window[k].reset()
    for value in values:
        if "tab" not in value:
            window[value].update("")
            window["id_info"].update("")


if __name__ == "__main__":
    main()
