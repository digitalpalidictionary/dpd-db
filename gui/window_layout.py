#!/usr/bin/env python3
import PySimpleGUI as sg
from tab_add_next_word import make_tab_add_next_word
from tab_add_word import make_tab_add_word
from tab_fix_sandhi import make_tab_fix_sandhi
from tab_db_tests import make_tab_db_tests


def window_layout():
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="darkgray",
        text_color="#00bfff",
        window_location=(0, 0),
        element_padding=(0, 3),
        margins=(0, 0),
    )

    tab_add_next_word = make_tab_add_next_word(sg)
    tab_add_word = make_tab_add_word(sg)
    tab_fix_sandhi = make_tab_fix_sandhi(sg)
    tab_db_tests = make_tab_db_tests(sg)

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", tab_add_next_word, key="tab_add_next_word"),
            sg.Tab("Add Word", tab_add_word, key="tab_add_word"),
            sg.Tab("Fix Sandhi", tab_fix_sandhi, key="tab_fix_sandhi"),
            sg.Tab("Test db", tab_db_tests, key="tab_db_tests")
        ]],
        key="tabgroup",
        enable_events=True,
        size=(None, None)
    )

    layout = [
        [tab_group],
        [sg.Text(
            "svāgataṃ", key="messages", text_color="white", font=(None, 12))]
    ]

    window = sg.Window(
        'Add new words',
        layout,
        resizable=True,
        size=(1280, 1080),
        finalize=True,
        )

    # bind enter key for quick search
    window['word_to_copy'].bind("<Return>", "_enter")
    window['book_to_add'].bind("<Return>", "_enter")
    window['search_for'].bind("<Return>", "_enter")
    window['contains'].bind("<Return>", "_enter")
    window['bold_1'].bind("<Return>", "_enter")
    window['add_construction'].bind("<Return>", "_enter")

    # bind tab keys to jump to next field in multiline elements
    window['meaning_1'].bind('<Tab>', '_tab', propagate=False)
    window['construction'].bind('<Tab>', '_tab', propagate=False)
    window['phonetic'].bind('<Tab>', '_tab', propagate=False)
    window['commentary'].bind('<Tab>', '_tab', propagate=False)
    window['example_1'].bind('<Tab>', '_tab', propagate=False)
    window['example_2'].bind('<Tab>', '_tab', propagate=False)

    return window
