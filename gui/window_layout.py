#!/usr/bin/env python3
import PySimpleGUI as sg
from db_helpers import get_next_ids
from tab_add_next_word import make_tab_add_next_word
from tab_add_word import make_tab_add_word
from tab_fix_sandhi import make_tab_fix_sandhi


def window_layout():
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="#faebd7",
        text_color="#00bfff",
        window_location=(0, 0)
    )

    tab_add_next_word = make_tab_add_next_word(sg)
    tab_add_word = make_tab_add_word(sg)
    tab_fix_sandhi = make_tab_fix_sandhi(sg)

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", tab_add_next_word, key="tab_add_next_word"),
            sg.Tab("Add Word", tab_add_word, key="tab_add_word"),
            sg.Tab("Fix Sandhi", tab_fix_sandhi, key="tab_fix_sandhi")
        ]],
        key="tabgroup",
        enable_events=True,
        size=(1080, 950)
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
        size=(1080, 1080),
        finalize=True,
        )

    window['word_to_copy'].bind("<Return>", "_enter")
    window['book_to_add'].bind("<Return>", "_enter")
    return window
