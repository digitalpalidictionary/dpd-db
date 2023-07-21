#!/usr/bin/env python3
import PySimpleGUI as sg
from tab_add_next_word import make_tab_add_next_word
from tab_edit_dpd import make_tab_edit_dpd
from tab_edit_dps import make_tab_edit_dps
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
    tab_edit_dpd = make_tab_edit_dpd(sg)
    tab_edit_dps = make_tab_edit_dps(sg)
    tab_fix_sandhi = make_tab_fix_sandhi(sg)
    tab_db_tests = make_tab_db_tests(sg)

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", tab_add_next_word, key="tab_add_next_word"),
            sg.Tab("Edit DPD", tab_edit_dpd, key="tab_edit_dpd"),
            sg.Tab("Edit DPS", tab_edit_dps, key="tab_edit_dps"),
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
    window['word_to_clone_edit'].bind("<Return>", "_enter")
    window['book_to_add'].bind("<Return>", "_enter")
    window['search_for'].bind("<Return>", "_enter")
    window['contains'].bind("<Return>", "_enter")
    window['bold_cc'].bind("<Return>", "_enter")
    window['bold_1'].bind("<Return>", "_enter")
    window['bold_2'].bind("<Return>", "_enter")
    window['add_construction'].bind("<Return>", "_enter")

    # bind tab keys to jump to next field in multiline elements
    window['meaning_1'].bind('<Tab>', '_tab', propagate=False)
    window['construction'].bind('<Tab>', '_tab', propagate=False)
    window['phonetic'].bind('<Tab>', '_tab', propagate=False)
    window['commentary'].bind('<Tab>', '_tab', propagate=False)
    window['example_1'].bind('<Tab>', '_tab', propagate=False)
    window['example_2'].bind('<Tab>', '_tab', propagate=False)

    # bind tab dps
    window['dps_ru_meaning'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_meaning'].bind('<Tab>', '_tab', propagate=False)
    window['dps_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_ru_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_notes'].bind('<Tab>', '_tab', propagate=False)
    window['dps_example_1'].bind('<Tab>', '_tab', propagate=False)
    window['dps_example_2'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_3'].bind('<Tab>', '_tab', propagate=False)
    window['dps_sbs_example_4'].bind('<Tab>', '_tab', propagate=False)

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

    return window
