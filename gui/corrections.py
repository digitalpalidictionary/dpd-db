#!/usr/bin/env python3
import PySimpleGUI as sg
from sqlalchemy import inspect

from db.get_db_session import get_db_session
from db.models import PaliWord


def main():

    db_session = get_db_session("dpd.db")
    column_names = get_column_names()
    window = make_window(column_names)

    while True:
        event, values = window.read()
        print(event, values)

        if event == "id_enter":
            db = db_session.query(PaliWord).filter(
                PaliWord.id == values["id"]).first()
            window["id_info"].update(
                f"{db.pali_1}: {db.pos}. {db.meaning_1}")

        if event == "field1":
            window["value1_old"].update(
                getattr(db, values["field1"]))

            if values["field1"] == "source_1":
                print("!")
                window["field2"].update("sutta_1")
                window["value2_old"].update(
                    getattr(db, "sutta_1"))
                window["field3"].update("example_1")
                window["value3_old"].update(
                    getattr(db, "example_1"))

        if event == "field2":
            window["value2_old"].update(
                getattr(db, values["field2"]))

        if event == "field3":
            window["value3_old"].update(
                getattr(db, values["field3"]))

        if event == sg.WIN_CLOSED:
            break

    window.close()


def make_window(column_names):
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="darkgray",
        text_color="#00bfff",
        # window_location=(500, 300),
        element_padding=(0, 3),
        margins=(0, 0),
    )

    make_corrections_tab = [
        [
            sg.Text("id", size=(15, 1)),
            sg.Input(
                "", key="id", size=(20, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Text("", key="id_info", size=(100, 1))
        ],
        [
            sg.Text("field1", size=(15, 1)),
            sg.Combo(
                column_names, key="field1", size=(20, 1),
                enable_events=True,),
        ],
        [
            sg.Text("value1", size=(15, 1)),
            sg.Multiline(
                "", key="value1_old", size=(50, 2)),
            sg.Multiline(
                "", key="value1_new", size=(50, 2))
        ],
        [
            sg.Text("comment1", size=(15, 1)),
            sg.Input(
                "", key="comment1", size=(100, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("field2", size=(15, 1)),
            sg.Combo(
                column_names, key="field2", size=(20, 1),
                enable_events=True),
        ],
        [
            sg.Text("value2", size=(15, 1)),
            sg.Multiline(
                "", key="value2_old", size=(50, 2)),
            sg.Multiline(
                "", key="value2_new", size=(50, 2))
        ],
        [
            sg.Text("comment2", size=(15, 1)),
            sg.Input(
                "", key="comment2", size=(100, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
        ],
        [
            sg.Text("field3", size=(15, 1)),
            sg.Combo(
                column_names, key="field3", size=(20, 1),
                enable_events=True),
            sg.Text("", size=(31, 1)),
            sg.Input(key="bold", size=(30, 1)),
            sg.Button("Bold", key="bold_button", font=(None, 13)),
        ],
        [
            sg.Text("value3", size=(15, 1)),
            sg.Multiline(
                "", key="value3_old", size=(50, 4)),
            sg.Multiline(
                "", key="value3_new", size=(50, 4))
        ],
        [
            sg.Text("comment3", size=(15, 1)),
            sg.Input(
                "", key="comment3", size=(100, 1)),
        ],
        [
            sg.Text("", size=(15, 1)),
            sg.Button(
                "Submit Correction", key="submit", size=(100, 1)),
        ],
    ]

    add_corrections_tab = [[]]

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
        'Corrections',
        layout,
        resizable=True,
        finalize=True,
        )

    window['id'].bind("<Return>", "_enter")
    window['field1'].bind("<Return>", "_enter")
    window['field2'].bind("<Return>", "_enter")
    window['field3'].bind("<Return>", "_enter")

    return window


def get_column_names():
    inspector = inspect(PaliWord)
    column_names = [column.name for column in inspector.columns]
    column_names = sorted(column_names)
    return column_names


if __name__ == "__main__":
    main()
