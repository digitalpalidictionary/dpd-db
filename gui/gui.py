#!/usr/bin/env python3
import PySimpleGUI as sg

from pathlib import Path
from typing import Dict
from rich import print

from db.db_helpers import print_column_names
from db.models import PaliWord
from helpers import add_word_to_db
from helpers import update_word_in_db

from helpers import Word
from helpers import copy_compound_from_db
from helpers import get_next_ids
from tools.pos import POS

# print_column_names(PaliWord)
# sg.main_sdk_help()


def main():
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 18)
    )
    #     button_color=("#c22b45", "#221a0e"),
    #     background_color="#221a0e",
    #     element_background_color="#221a0e",
    #     text_element_background_color="#221a0e",
    #     input_elements_background_color="#221a0e",
    #     input_text_color="tan",
    #     text_color="#9b794b",
    #     titlebar_background_color="#362712",
    #     titlebar_text_color="#9b794b",
    #     icon="../favicon/favicon_io nu circle/apple-touch-icon.png",

    id, user_id = get_next_ids()

    add_compounds_layout = [
        [
            sg.Text('id', size=(15, 1)),
            sg.Input(f"{id}", key="id", size=(20, 1)),
            sg.Text('user_id'),
            sg.Input(f"{user_id}", key="user_id", size=(21, 1))
        ],
        [
            sg.Text('pali_1', size=(15, 1)),
            sg.Input(key="pali_1", size=(50, 1))
        ],
        [
            sg.Text('pali_2', size=(15, 1)),
            sg.Input(key="pali_2", size=(50, 1))
        ],
        [
            sg.Text('pos', size=(15, 1)),
            sg.Combo(POS, key="pos", size=(7, 1)),
        ],
        [
            sg.Text('grammar', size=(15, 1)),
            sg.Input(key="grammar", size=(50, 1))
        ],
        [
            sg.Text('neg', size=(15, 1)),
            sg.Input(key="neg", size=(7, 1)),
            sg.Text('case'),
            sg.Input(key="plus_case", size=(15, 1))
        ],
        [
            sg.Text('meaning_1', size=(15, 2)),
            sg.Multiline(key="meaning_1", size=(50, 2), no_scrollbar=True)
        ],
        [
            sg.Text('meaning_lit', size=(15, 1)),
            sg.Input(key="meaning_lit", size=(50, 1))
        ],
        [
            sg.Text('family_compound', size=(15, 1)),
            sg.Input(key="family_compound", size=(50, 1))
        ],
        [
            sg.Text('family_set', size=(15, 1)),
            sg.Input(key="family_set", size=(50, 1))
        ],
        [
            sg.Text('construction', size=(15, 1)),
            sg.Input(key="construction", size=(50, 1))
        ],
        [
            sg.Text('compound_type', size=(15, 1)),
            sg.Input(key="compound_type", size=(10, 1)),
            sg.Text('constr'),
            sg.Input(key="compound_construction", size=(32, 1)),
        ],
        [
            sg.Text('antonym', size=(15, 1)),
            sg.Input(key="antonym", size=(50, 1))
        ],
        [
            sg.Text('synonym', size=(15, 1)),
            sg.Input(key="synonym", size=(50, 1))
        ],
        [
            sg.Text('variant', size=(15, 1)),
            sg.Input(key="variant", size=(50, 1))
        ],
        [
            sg.Text('commentary', size=(15, 4)),
            sg.Multiline(key="commentary", size=(50, 4), no_scrollbar=True)
        ],
        [
            sg.Text('stem pattern', size=(15, 1)),
            sg.Input(key="stem", size=(20, 1), justification="r"),
            sg.Input(key="pattern", size=(17, 1)),
            sg.Input("pass1", key="origin", size=(10, 1))
        ],
        ]

    tab1_layout = [
        [
            sg.Frame("", add_compounds_layout, expand_x=True)
        ],
        [
            sg.Button('Copy'),
            sg.Input(
                key="compound_to_copy",
                size=(15, 1),
                enable_events=True,
                ),
            sg.Button("Clear"),
            sg.Button("Add to db", key="add_compound_to_db"),
            sg.Button("Update", key="update_compound"),
            sg.Button("Debug"),
            sg.Button("Close")
        ]
    ]

    tab2_layout = [
        []
    ]

    layout = [[
        sg.TabGroup(
            [[
                sg.Tab("Add Compound", tab1_layout),
                sg.Tab('Add Root', tab2_layout),
            ]], key="tabgroup", enable_events=True,
        )
    ]]

    window = sg.Window(
        'Add new words',
        layout,
        resizable=True,
        finalize=True
        )
    window['compound_to_copy'].bind("<Return>", "_Enter")

    while True:
        event, values = window.read()

        if event:
            print(f"{event=}")
            print(f"{values=}")

        if event == "Copy" or event == "compound_to_copy_Enter":
            values, window = copy_compound_from_db(sg, values, window)

        if event == "Clear":
            for value in values:
                print(value)
                if not isinstance(value, int):
                    if not any(c.isupper() for c in value):
                        window[value].update("")

            id, user_id = get_next_ids()
            window["id"].update(id)
            window["user_id"].update(user_id)

        if event == "add_compound_to_db":
            add_word_to_db(values, sg)

        if event == "update_compound":
            update_word_in_db(values, sg)

        if event == "Debug":
            print(f"{values}")

        if event == "Close" or event == sg.WIN_CLOSED:
            break

    window.close()


if __name__ == "__main__":
    main()
