#!/usr/bin/env python3

"""Render all tabs into main window."""


import PySimpleGUI as sg
from tab_add_next_word import make_tab_add_next_word
from tab_edit_dpd import make_tab_edit_dpd
from tab_edit_dps import make_tab_edit_dps
from tab_fix_sandhi import make_tab_fix_sandhi
from tab_db_tests import make_tab_db_tests
from tab_dps_tests import make_tab_dps_tests
from functions import load_gui_config

config = load_gui_config()

def window_layout(primary_user):

    # Get screen width and height
    screen_width, screen_height = sg.Window.get_screen_size()

    # Calculate width and height of the screen
    window_width = int(screen_width * config["screen_fraction_width"])
    window_height = int(screen_height * config["screen_fraction_height"])


    sg.theme(config["theme"])
    sg.set_options(
        font=config["font"],
        input_text_color=config["input_text_color"],
        text_color=config["text_color"],
        window_location=config["window_location"],
        element_padding=config["element_padding"],
        margins=config["margins"],
    )

    tab_add_next_word = make_tab_add_next_word(sg, primary_user)
    tab_edit_dpd = make_tab_edit_dpd(sg, primary_user)
    tab_edit_dps = make_tab_edit_dps(sg)
    tab_fix_sandhi = make_tab_fix_sandhi(sg)
    tab_db_tests = make_tab_db_tests(sg, primary_user)
    tab_dps_tests = make_tab_dps_tests(sg)


    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", tab_add_next_word, key="tab_add_next_word"),
            sg.Tab("Edit DPD", tab_edit_dpd, key="tab_edit_dpd"),
            sg.Tab("Edit DPS", tab_edit_dps, key="tab_edit_dps"),
            sg.Tab("Fix Sandhi", tab_fix_sandhi, key="tab_fix_sandhi"),
            sg.Tab("Test db", tab_db_tests, key="tab_db_tests"),
            sg.Tab("Test DPS", tab_dps_tests, key="tab_dps_tests")
        ]],
        key="tabgroup",
        enable_events=True,
    )

    layout = [
        [sg.Text(
            "svāgataṃ", key="messages", text_color="white", font=(None, 12))],
        [tab_group],
    ]

    window = sg.Window(
        'Add new words',
        layout,
        resizable=True,
        size=(window_width, window_height),
        finalize=True,
    )


    # bind enter key for quick search
    window['word_to_clone_edit'].bind("<Return>", "_enter")
    window['book_to_add'].bind("<Return>", "_enter")
    window['search_for'].bind("<Return>", "_enter")
    window['contains'].bind("<Return>", "_enter")
    window['bold_cc'].bind("<Return>", "_enter")
    window['bold_1'].bind("<Return>", "_enter")
    window['bold_2'].bind("<Return>", "_enter")
    window['add_construction'].bind("<Return>", "_enter")

    # bind enter key dps
    window['dps_bold_1'].bind("<Return>", "_enter")
    window['dps_bold_2'].bind("<Return>", "_enter")
    window['dps_bold_3'].bind("<Return>", "_enter")
    window['dps_bold_4'].bind("<Return>", "_enter")

    # bind tab keys to jump to next field in multiline elements
    window['meaning_1'].bind('<Tab>', '_tab', propagate=False)
    window['construction'].bind('<Tab>', '_tab', propagate=False)
    window['phonetic'].bind('<Tab>', '_tab', propagate=False)
    window['commentary'].bind('<Tab>', '_tab', propagate=False)
    window['example_1'].bind('<Tab>', '_tab', propagate=False)
    window['example_2'].bind('<Tab>', '_tab', propagate=False)

    # bind tab dps
    window['dps_meaning'].bind('<Tab>', '_tab', propagate=False)
    window['dps_ru_online_suggestion'].bind('<Tab>', '_tab', propagate=False)
    window['dps_notes_online_suggestion'].bind('<Tab>', '_tab', propagate=False)
    window['dps_ru_meaning'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_meaning'].bind('<Tab>', '_tab', propagate=False)
    window['dps_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_ru_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_example_1'].bind('<Tab>', '_tab', propagate=False)
    window['dps_example_2'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_1'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_2'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_3'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_4'].bind('<Tab>', '_tab', propagate=False)
    window['online_suggestion'].bind('<Tab>', '_tab', propagate=False)

    # completition combo bindings
    window["pos"].bind("<Return>", "-enter")
    window["pos"].bind("<Key>", "-key")
    window["pos"].bind("<FocusOut>", "-focus_out")

    window["neg"].bind("<Return>", "-enter")
    window["neg"].bind("<Key>", "-key")
    window["neg"].bind("<FocusOut>", "-focus_out")

    window["verb"].bind("<Return>", "-enter")
    window["verb"].bind("<Key>", "-key")
    window["verb"].bind("<FocusOut>", "-focus_out")

    window["trans"].bind("<Return>", "-enter")
    window["trans"].bind("<Key>", "-key")
    window["trans"].bind("<FocusOut>", "-focus_out")

    window["plus_case"].bind("<Return>", "-enter")
    window["plus_case"].bind("<Key>", "-key")
    window["plus_case"].bind("<FocusOut>", "-focus_out")

    window["root_key"].bind("<Return>", "-enter")
    window["root_key"].bind("<Key>", "-key")
    window["root_key"].bind("<FocusOut>", "-focus_out")

    # window["family_root"].bind("<Return>", "-enter")
    # window["family_root"].bind("<Key>", "-key")
    # window["family_root"].bind("<FocusOut>", "-focus_out")

    # window["root_sign"].bind("<Return>", "-enter")
    # window["root_sign"].bind("<Key>", "-key")
    # window["root_sign"].bind("<FocusOut>", "-focus_out")

    # window["root_base"].bind("<Return>", "-enter")
    # window["root_base"].bind("<Key>", "-key")
    # window["root_base"].bind("<FocusOut>", "-focus_out")

    window["family_word"].bind("<Return>", "-enter")
    window["family_word"].bind("<Key>", "-key")
    window["family_word"].bind("<FocusOut>", "-focus_out")

    window["derivative"].bind("<Return>", "-enter")
    window["derivative"].bind("<Key>", "-key")
    window["derivative"].bind("<FocusOut>", "-focus_out")

    window["compound_type"].bind("<Return>", "-enter")
    window["compound_type"].bind("<Key>", "-key")
    window["compound_type"].bind("<FocusOut>", "-focus_out")

    window["family_set"].bind("<Return>", "-enter")
    window["family_set"].bind("<Key>", "-key")
    window["family_set"].bind("<FocusOut>", "-focus_out")

    window["pattern"].bind("<Return>", "-enter")
    window["pattern"].bind("<Key>", "-key")
    window["pattern"].bind("<FocusOut>", "-focus_out")

    # dps CompletionCombo
    window["dps_id_or_pali_1"].bind("<Return>", "_enter")

    window["dps_sbs_chant_pali_1"].bind("<Return>", "-enter")
    window["dps_sbs_chant_pali_1"].bind("<Key>", "-key")
    window["dps_sbs_chant_pali_1"].bind("<FocusOut>", "-focus_out")

    window["dps_sbs_chant_pali_2"].bind("<Return>", "-enter")
    window["dps_sbs_chant_pali_2"].bind("<Key>", "-key")
    window["dps_sbs_chant_pali_2"].bind("<FocusOut>", "-focus_out")

    window["dps_sbs_chant_pali_3"].bind("<Return>", "-enter")
    window["dps_sbs_chant_pali_3"].bind("<Key>", "-key")
    window["dps_sbs_chant_pali_3"].bind("<FocusOut>", "-focus_out")

    window["dps_sbs_chant_pali_4"].bind("<Return>", "-enter")
    window["dps_sbs_chant_pali_4"].bind("<Key>", "-key")
    window["dps_sbs_chant_pali_4"].bind("<FocusOut>", "-focus_out")

    window["dps_sbs_class_anki"].bind("<Return>", "-enter")
    window["dps_sbs_class_anki"].bind("<Key>", "-key")
    window["dps_sbs_class_anki"].bind("<FocusOut>", "-focus_out")

    window["dps_sbs_category"].bind("<Return>", "-enter")
    window["dps_sbs_category"].bind("<Key>", "-key")
    window["dps_sbs_category"].bind("<FocusOut>", "-focus_out")

    return window
