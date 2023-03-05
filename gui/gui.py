#!/usr/bin/env python3
import PySimpleGUI as sg
import sys

from rich import print

from helpers import add_word_to_db
from helpers import update_word_in_db
from helpers import copy_compound_from_db
from helpers import get_next_ids
from db.db_helpers import print_column_names
from db.models import PaliWord
from tools.pos import POS

# print_column_names(PaliWord)
# sg.main_sdk_help()


def main():
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        icon="gui/icons/logo.png",
        # input_elements_background_color="#221a0e",
        input_text_color="#faebd7",
        text_color="#00bfff",
    )

    id, user_id = get_next_ids()

    words_to_add = ["dog", "parrot", "pidgeon"]

    tab1_layout = [
        [
            sg.Text("")
        ],
        [
            sg.Text('next word to add', size=(15, 1, )),
            sg.Input(
                f'{words_to_add[0]}',
                use_readonly_for_disable=True,
                key='next_word_to_add',
                text_color="#faebd7",
                selected_text_color="black",
                selected_background_color="SteelBlue",
            ),
            sg.Text(f"{len(words_to_add)}")
        ],
        [
            sg.Text("", size=(15, 1, )),
            sg.Radio("sandhi ok", 1, key="sandhi_ok",
                     size=(50, 1), enable_events=True),
        ],
        [
            sg.Text("", size=(15, 1, )),
            sg.Radio(
                "add a compound word", 1,
                key="add_to_compounds", size=(50, 1),
                enable_events=True
            ),
        ],
        [
            sg.Text("", size=(15, 1, )),
            sg.Radio(
                "add a root or non-compound", 1,
                key="add_to_roots", size=(50, 1)),
        ],
        [
            sg.Text("", size=(15, 1, )),
            sg.Radio(
                "pass", 1,
                key="pass", size=(50, 1)),
        ],
    ]

    # tab1_layout = [
    #     [
    #         sg.Column(
    #             add_words_layout,
    #         ),
    #     ],
    # ]

    add_compounds_layout = [
        [
            sg.Text('id', size=(15, 1, )),
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
            sg.Text(
                'pos',
                size=(15, 1)),
            sg.Combo(
                POS,
                key="pos",
                size=(7, 1),
                enable_events=False),
        ],
        [
            sg.Text('grammar', size=(15, 1)),
            sg.Input(key="grammar", size=(50, 1))
        ],
        [
            sg.Text('derived_from', size=(15, 1)),
            sg.Input(key="derived_from", size=(50, 1))
        ],
        # [
        #     sg.Text('verb', size=(15, 1)),
        #     sg.Input(key="verb", size=(7, 1)),
        #     sg.Text('trans'),
        #     sg.Input(key="trans", size=(15, 1))
        # ],
        [
            sg.Text('neg', size=(15, 1)),
            sg.Input(key="neg", size=(7, 1)),
            sg.Text('case '),
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
            sg.Text('meaning_2', size=(15, 1)),
            sg.Input(key="meaning_2", size=(50, 1))
        ],
        # [
        #     sg.Text('root_key', size=(15, 1)),
        #     sg.Input(key="root_key", size=(10, 1)),
        #     sg.Text('family_root'),
        #     sg.Input(key="family_root", size=(28, 1)),

        # ],
        # [
        #     sg.Text('root_sign', size=(15, 1)),
        #     sg.Input(key="root_sign", size=(10, 1)),
        #     sg.Text('root_base  '),
        #     sg.Input(key="root_base", size=(28, 1)),
        # ],
        # [
        #     sg.Text('family_word', size=(15, 1)),
        #     sg.Input(key="family_word", size=(50, 1))
        # ],
        [
            sg.Text('family_compound', size=(15, 1)),
            sg.Input(key="family_compound", size=(50, 1))
        ],
        [
            sg.Text('construction', size=(15, 1)),
            sg.Input(key="construction", size=(50, 1))
        ],
        [
            sg.Text('derivative', size=(15, 1)),
            sg.Input(key="derivative", size=(10, 1)),
            sg.Text('suffix'),
            sg.Input(key="suffix", size=(33, 1)),
        ],
        [
            sg.Text('phonetic', size=(15, 1)),
            sg.Multiline(key="phonetic", size=(50, 1), no_scrollbar=True)
        ],
        [
            sg.Text('compound_type', size=(15, 1)),
            sg.Input(key="compound_type", size=(50, 1)),
        ],
        [
            sg.Text('compound_construction', size=(15, 1)),
            sg.Input(key="compound_construction", size=(50, 1)),
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
            sg.Text('notes', size=(15, 1)),
            sg.Input(key="notes", size=(50, 41))
        ],
        [
            sg.Text('non_ia', size=(15, 1)),
            sg.Input(key="non_ia", size=(50, 41))
        ],
        [
            sg.Text('sanskrit', size=(15, 1)),
            sg.Input(key="sanskrit", size=(50, 1))
        ],
        [
            sg.Text('cognate', size=(15, 1)),
            sg.Input(key="cognate", size=(50, 1))
        ],
        [
            sg.Text('link', size=(15, 1)),
            sg.Input(key="link", size=(50, 1))
        ],
        [
            sg.Text('source_1', size=(15, 1)),
            sg.Input(key="source_1", size=(50, 1)),
        ],
        [
            sg.Text('sutta_1', size=(15, 1)),
            sg.Input(key="sutta_1", size=(50, 1)),
        ],
        [
            sg.Text('example_1', size=(15, 4)),
            sg.Multiline(key="example_1", size=(50, 4), no_scrollbar=True)
        ],
        [
            sg.Text('bold_1', size=(15, 1)),
            sg.Input(key="bold_1", size=(50, 1))
        ],
        [
            sg.Text('source_2', size=(15, 1)),
            sg.Input(key="source_2", size=(50, 1)),
        ],
        [
            sg.Text('sutta_2', size=(15, 1)),
            sg.Input(key="sutta_2", size=(50, 1)),
        ],
        [
            sg.Text('example_2', size=(15, 4)),
            sg.Multiline(key="example_2", size=(50, 4), no_scrollbar=True)
        ],
        [
            sg.Text('bold_2', size=(15, 1)),
            sg.Input(key="bold_2", size=(50, 1))
        ],
        [
            sg.Text('family_set', size=(15, 1)),
            sg.Input(key="family_set", size=(50, 1))
        ],
        [
            sg.Text('stem pattern', size=(15, 1)),
            sg.Input(key="stem", size=(20, 1), justification="r"),
            sg.Input(key="pattern", size=(17, 1)),
            sg.Input("pass1", key="origin", size=(10, 1))
        ],
        ]

    helper_layout = [[
        sg.Multiline(
            "",
            key='message_display',
            size=(25, 27),
            autoscroll=True,
            expand_y=True
        ),
    ]]

    tab2_layout = [
        [
            sg.Column(
                add_compounds_layout,
                scrollable=True,
                vertical_scroll_only=True,
                expand_y=True,
            ),
            sg.Column(
                helper_layout,
                expand_y=True,
            ),
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

    tab3_layout = [
        []
    ]

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Add Word", tab1_layout, key="tab1"),
            sg.Tab("Add Compound", tab2_layout, key="tab2"),
            sg.Tab('Add Root', tab3_layout, key="tab3"),
        ]], key="tabgroup", enable_events=True,
    )

    layout = [[tab_group]]

    window = sg.Window(
        'Add new words',
        layout,
        resizable=True,
        size=(1920, 1080),
        finalize=True,
        )

    window['compound_to_copy'].bind("<Return>", "_Enter")

    while True:
        # sys.stdout = window['message_display']

        event, values = window.read()

        if event:
            print(f"{event=}")
            print(f"{values=}")

        if event == "add_to_compounds":
            window["tab2"].select()


        if event == "pos":
            window["message_display"].update("x")

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
            window["origin"].update("pass1")

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
