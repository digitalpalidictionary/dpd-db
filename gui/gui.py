#!/usr/bin/env python3.10
import PySimpleGUI as sg

from rich import print
from window_layout import window_layout
from db_helpers import add_word_to_db
from db_helpers import update_word_in_db
from db_helpers import get_next_ids
from db_helpers import dpd_values_list

from functions.copy_word_from_db import copy_word_from_db
from functions.open_in_goldendict import open_in_goldendict
from functions.sandhi_ok import sandhi_ok
from functions.make_words_to_add_list import make_words_to_add_list
from functions.add_sandhi_rule import add_sandhi_rule, open_sandhi_rules
from functions.add_sandhi_correction import add_sandhi_correction
from functions.add_sandhi_correction import open_sandhi_corrections
from functions.add_spelling_mistake import add_spelling_mistake
from functions.add_spelling_mistake import open_spelling_mistakes
from functions.add_variant_reading import add_variant_reading
from functions.add_variant_reading import open_variant_readings
from functions.open_inflection_tables import open_inflection_tables

# sg.main_sdk_help()


def main():
    window = window_layout()

    while True:
        # sys.stdout = window['message_display']

        event, values = window.read()
        if event:
            print(f"{event=}")
            print(f"{values=}")

        # add book

        if event == "book_to_add_enter" or event == "books_to_add_button":
            words_to_add_list = make_words_to_add_list(
                window, values["book_to_add"])

            if words_to_add_list != []:
                window["word_to_add"].update(words_to_add_list)
                window["words_to_add_length"].update(len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    f"all missing words from {values['book_to_add']} added",
                    text_color="white")
            else:
                window["messages"].update(
                    "empty list, try again", text_color="red")

        # open word in goldendict

        if event == "word_to_add":
            if values["word_to_add"] != []:
                open_in_goldendict(values["word_to_add"][0])

        # sandhi ok

        if event == "sandhi_ok":
            print(values)
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                sandhi_ok(window, values["word_to_add"][0])
                if values["word_to_add"][0] in words_to_add_list:
                    words_to_add_list.remove(values["word_to_add"][0])
                window["word_to_add"].update(words_to_add_list)
                window["words_to_add_length"].update(len(words_to_add_list))
                open_in_goldendict(words_to_add_list[0])

        # add word

        if event == "add_word":
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                window["tab_add_word"].select()
                window["pali_1"].update(values["word_to_add"][0])
                window["messages"].update("adding word", text_color="white")

        # fix sandhi

        if event == "fix_sandhi":
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                window["tab_fix_sandhi"].select()
                window["example"].update(values["word_to_add"][0])
                window["sandhi_to_correct"].update(values["word_to_add"][0])
                window["spelling_mistake"].update(values["word_to_add"][0])
                window["variant_reading"].update(values["word_to_add"][0])

        if event == "update_inflection_templates":
            open_inflection_tables()

        # add word events

        if event == "Copy" or event == "word_to_copy_enter":
            values, window = copy_word_from_db(sg, values, window)

        if event == "Clear":
            for value in values:
                if value in dpd_values_list:
                    window[value].update("")

            id, user_id = get_next_ids()
            window["id"].update(id)
            window["user_id"].update(user_id)
            window["origin"].update("pass1")

        if event == "add_word_to_db":
            add_word_to_db(window, values)

        if event == "update_word":
            update_word_in_db(window, values)

        if event == "Debug":
            print(f"{values}")

        if event == "Close" or event == sg.WIN_CLOSED:
            break

        # fix sandhi events

        # sandhi rules

        if event == "add_sandhi_rule":
            add_sandhi_rule(window, values)

        if event == "open_sandhi_rules":
            open_sandhi_rules()

        # sandhi corrections

        if event == "add_sandhi_correction":
            add_sandhi_correction(window, values)

        if event == "open_sandhi_corrections":
            open_sandhi_corrections()

        # spelling mistakes

        if event == "add_spelling_mistake":
            add_spelling_mistake(window, values)

        if event == "open_spelling_mistakes":
            open_spelling_mistakes()

        # variant readings

        if event == "add_variant_reading":
            add_variant_reading(window, values)

        if event == "open_variant_readings":
            open_variant_readings()

    window.close()


if __name__ == "__main__":
    main()
