#!/usr/bin/env python3
import PySimpleGUI as sg
from rich import print
from tab_edit_dps import make_tab_edit_dps

from functions_db import fetch_id_or_pali
from functions_db import fetch_ru
from functions_db import fetch_sbs
from functions_db import dps_update_db

from functions import open_in_goldendict
from functions import populate_dps_tab
from functions import update_sbs_chant
from functions import clear_dps


def main():
    # db_session = get_db_session("dpd.db")
    sg.theme('DarkGrey10')
    sg.set_options(
        font=("Noto Sans", 16),
        input_text_color="darkgray",
        text_color="#00bfff",
        window_location=(0, 0),
        element_padding=(0, 3),
        margins=(0, 0),
    )

    tab_edit_dps = make_tab_edit_dps(sg)

    tab_group = sg.TabGroup(
        [[
            sg.Tab("Words To Add", [[]], key="tab_add_next_word"),
            sg.Tab("Edit DPD", [[]], key="tab_edit_dpd"),
            sg.Tab("Edit DPS", tab_edit_dps, key="tab_edit_dps"),
            sg.Tab("Fix Sandhi", [[]], key="tab_fix_sandhi"),
            sg.Tab("Test db", [[]], key="tab_db_tests")
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

    window["tab_edit_dps"].select()
    window["dps_id_or_pali_1"].bind("<Return>", "_enter")

    while True:
        event, values = window.read()

        if event:
            print(f"{event}")
            print(f"{values}")

        elif event == sg.WIN_CLOSED:
            break

        # tabs jumps to next field in multiline
        if event == "meaning_1_tab":
            window['meaning_1'].get_next_focus().set_focus()
        elif event == "construction_tab":
            window['construction'].get_next_focus().set_focus()
        elif event == "phonetic_tab":
            window['phonetic'].get_next_focus().set_focus()
        elif event == "commentary_tab":
            window['commentary'].get_next_focus().set_focus()
        elif event == "example_1_tab":
            window['example_1'].get_next_focus().set_focus()
        elif event == "example_2_tab":
            window['example_2'].get_next_focus().set_focus()

        # combo events

        elif event.endswith("-key"):
            combo = window[event.replace("-key", "")]
            combo.filter()

        elif event.endswith("-enter"):
            combo = window[event.replace("-enter", "")]
            combo.complete()

        elif event.endswith("-focus_out"):
            combo = window[event.replace("-focus_out", "")]
            combo.hide_tooltip()

        # dps_events
        if (
            event == "dps_id_or_pali_1_enter" or
            event == "dps_id_or_pali_1_button"
        ):
            if values["dps_id_or_pali_1"]:
                dpd_word = fetch_id_or_pali(values)
                if dpd_word:
                    ru_word = fetch_ru(dpd_word.id)
                    sbs_word = fetch_sbs(dpd_word.id)
                    open_in_goldendict(dpd_word.pali_1)
                    populate_dps_tab(
                        values, window, dpd_word, ru_word, sbs_word)
                else:
                    window["messages"].update(
                        "not a valid id or pali_1", text_color="red")

        if event == "dps_sbs_chant_pali_1":
            chant = values["dps_sbs_chant_pali_1"]
            update_sbs_chant(1, chant, window)

        elif event == "dps_sbs_chant_pali_2":
            update_sbs_chant(
                2, values["dps_sbs_chant_pali_2"], window)

        elif event == "dps_sbs_chant_pali_3":
            update_sbs_chant(
                3, values["dps_sbs_chant_pali_3"], window)

        elif event == "dps_sbs_chant_pali_4":
            update_sbs_chant(
                4, values["dps_sbs_chant_pali_4"], window)

        elif event == "dps_clear_button":
            clear_dps(values, window)

        elif event == "dps_update_db_button":
            dps_update_db(
                values, window, dpd_word, ru_word, sbs_word)
            clear_dps(values, window)

        elif event == "dps_reset_button":
            if dpd_word:
                clear_dps(values, window)
                populate_dps_tab(
                            values, window, dpd_word, ru_word, sbs_word)
            else:
                window["messages"].update(
                        "not a valid id or pali_1", text_color="red")

    window.close()


if __name__ == "__main__":
    main()
