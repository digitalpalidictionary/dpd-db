#!/usr/bin/env python3.11
import PySimpleGUI as sg
import re
import pandas as pd
import pickle

from rich import print

from window_layout import window_layout
from db_helpers import add_word_to_db
from db_helpers import update_word_in_db
from db_helpers import get_next_ids
from db_helpers import get_family_root_values
from db_helpers import get_root_sign_values
from db_helpers import get_root_base_values
from db_helpers import get_synonyms
from db_helpers import get_sanskrit
from db_helpers import copy_word_from_db
from db_helpers import edit_word_in_db
from functions import get_paths
from functions import open_in_goldendict
from functions import sandhi_ok
from functions import make_words_to_add_list
from functions import add_sandhi_rule, open_sandhi_rules
from functions import add_sandhi_correction
from functions import open_sandhi_corrections
from functions import add_spelling_mistake
from functions import open_spelling_mistakes
from functions import add_variant_reading
from functions import open_variant_readings
from functions import open_inflection_tables
from functions import find_sutta_example
from functions import find_commentary_defintions
from functions import run_internal_tests
from functions import open_internal_tests
from functions import check_spelling
from functions import add_spelling
from functions import edit_spelling
from functions import clear_errors
from functions import clear_values
from functions import add_stem_pattern
from functions import Flags, reset_flags
from functions import display_summary
from tools.pos import DECLENSIONS, VERBS
from scripts.backup_to_tsv import backup_db_to_tsvs
from scripts.anki_csvs import export_anki_csvs


def main():
    pth = get_paths()
    # !!! this is slow !!!
    definitions_df = pd.read_csv(pth.defintions_csv_path, sep="\t")
    window = window_layout()
    flags = Flags()
    get_next_ids(window)

    while True:
        event, values = window.read()

        if event:
            print(f"{event=}")
            print(f"{values=}")

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
                window["search_for"].update(values["word_to_add"][0])
                window["bold_1"].update(values["word_to_add"][0])
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

        if event == "pali_2":
            if flags.pali_2:
                window["pali_2"].update(f"{values['pali_1']}")
                flags.pali_2 = False

        if event == "grammar":
            if flags.grammar:
                if values["pos"] in VERBS:
                    window["grammar"].update(f"{values['pos']} of ")
                else:
                    window["grammar"].update(f"{values['pos']}, ")
                flags.grammar = False

        if event == "derived_from":
            if flags.derived_from:
                if " of " in values["grammar"] or " from " in values["grammar"]:
                    derived_from = re.sub(
                        ".+( of | from )(.+)(,|$)", r"\2", values["grammar"])
                    window["derived_from"].update(derived_from)
                    flags.derived_from = False

        if event == "meaning_1":
            field = "meaning_1"
            error_field = "meaning_1_error"
            check_spelling(field, error_field, values, window)

        if event == "meaning_lit":
            field = "meaning_lit"
            error_field = "meaning_lit_error"
            check_spelling(field, error_field, values, window)

        if event == "meaning_lit":
            field = "meaning_lit"
            error_field = "meaning_lit_error"
            check_spelling(field, error_field, values, window)

        if event == "meaning_2":
            field = "meaning_2"
            error_field = "meaning_2_error"
            check_spelling(field, error_field, values, window)

        if event == "add_spelling_button":
            word = values["add_spelling"]
            add_spelling(word)
            window["messages"].update(f"{word} added to dictionary")

        if event == "edit_spelling_button":
            edit_spelling()

        if event == "family_root" and values["root_key"] != "":
            if flags.family_root:
                root_key = values["root_key"]
                FAMILY_ROOT_VALUES = get_family_root_values(root_key)
                window["family_root"].update(values=FAMILY_ROOT_VALUES)
                flags.family_root = False

        if event == "root_sign":
            if flags.root_sign:
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                flags.root_sign = False

        if event == "root_base":
            if flags.root_base:
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                flags.root_base = False

        if event == "family_compound":
            if flags.family_compound:
                window["family_compound"].update(values["pali_1"])
                flags.family_compound = False

        if event == "construction":
            if flags.construction:
                if values["root_key"] != "":
                    family = values["family_root"].replace(" ", " + ")
                    neg = ""
                    if values["neg"] != "":
                        neg = "na + "
                    if values["root_base"] != "":
                        # remove (end brackets)
                        base = re.sub(r" \(.+\)$", "", values["root_base"])
                        # remove front
                        base = re.sub("^.+> ", "", base)
                        family = re.sub("√.+", base, family)
                    window["construction"].update(f"{neg}{family} + ")

                elif "comp" in values["grammar"]:
                    window["construction"].update(values["pali_1"])

                flags.construction = False

        if event == "derivative":
            print("hello")
            "ptp" in values["grammar"]
            if "ptp" in values["grammar"]:
                window["derivative"].update("kicca")

        if event == "suffix":
            if flags.suffix and values["pos"] in DECLENSIONS:
                if "comp" not in values["grammar"]:
                    suffix = values["construction"]
                    suffix = re.sub(r"\n.+", "", suffix)
                    suffix = re.sub(r".+ \+ ", "", suffix)
                    window["suffix"].update(suffix)
                flags.suffix = False

        if event == "compound_construction":
            if (values["compound_type"] != "" and
                    flags.compound_construction):
                window["compound_construction"].update(values["construction"])
                flags.compound_construction = False

        if event == "bold_cc_button":
            cc_bold = re.sub(
                values["bold_cc"],
                f"<b>{values['bold_cc']}</b>",
                values["compound_construction"])
            window["compound_construction"].update(cc_bold)
            window["bold_cc"].update("")

        if ((event == "example_1" and flags.example_1) or
            (event == "source_1" and flags.example_1) or
            (event == "sutta_1" and flags.example_1) or
                event == "another_eg_1"):

            if values["book_to_add"] == "" or values["word_to_add"] == []:
                book_to_add = sg.popup_get_text("Which book?", title="Book")
                values["book_to_add"] = book_to_add
                values["word_to_add"] = [values["pali_1"][:-2]]
            sutta_sentences = find_sutta_example(sg, values)
            window["source_1"].update(sutta_sentences["source_1"])
            window["sutta_1"].update(sutta_sentences["sutta_1"])
            window["example_1"].update(sutta_sentences["example_1"])
            flags.example_1 = False

        if event == "bold_1_button":
            example_1_bold = re.sub(
                values["bold_1"],
                f"<b>{values['bold_1']}</b>",
                values["example_1"])
            window["example_1"].update(example_1_bold)
            window["bold_1"].update("")

        if event == "another_eg_2":
            if values["book_to_add"] == "":
                window["source_2_error"].update(
                    "no book to add", text_color="red")
            elif values["word_to_add"] == []:
                window["source_2_error"].update(
                    "no word to add", text_color="red")
            else:
                sutta_sentences = find_sutta_example(sg, values)
                window["source_2"].update(sutta_sentences["source_1"])
                window["sutta_2"].update(sutta_sentences["sutta_1"])
                window["example_2"].update(sutta_sentences["example_1"])
                flags.example_1 = False

        if event == "bold_2_button":
            example_2_bold = re.sub(
                values["bold_2"],
                f"<b>{values['bold_2']}</b>",
                values["example_2"])
            window["example_2"].update(example_2_bold)
            window["bold_2"].update("")

        if event == "synonym":
            if flags.synoyms:
                synoyms = get_synonyms(values["pos"], values["meaning_1"])
                window["synonym"].update(synoyms)
                flags.synoyms = False

        if event == "defintions_search_button":
            commentary_defintions = find_commentary_defintions(
                sg, values, definitions_df)
            if commentary_defintions:
                commentary = ""
                for c in commentary_defintions:
                    commentary += f"({c['ref_code']}) {c['commentary']}\n"
                commentary = commentary.rstrip("\n")
                window["commentary"].update(commentary)

        if event == "sanskrit":
            if flags.sanskrit and re.findall(r"\bcomp\b", values["grammar"]) != []:
                sanskrit = get_sanskrit(values["construction"])
                window["sanskrit"].update(sanskrit)
                flags.sanskrit = False

        if event == "stem":
            if flags.stem:
                add_stem_pattern(values, window)
                flags.stem = False

        # add word buttons

        if event == "Copy" or event == "word_to_copy_enter":
            if values["word_to_copy"] != "":
                copy_word_from_db(values, window)
            else:
                window["messages"].update("No word to copy!", text_color="red")

        if event == "edit_button":
            if values["word_to_copy"] != "":
                edit_word_in_db(values, window)
            else:
                window["messages"].update("No word to edit!", text_color="red")

        if event == "Clear":
            clear_errors(window)
            clear_values(values, window)
            get_next_ids(window)
            reset_flags(flags)
            window["messages"].update("")

        if event == "test_internal":
            clear_errors(window)
            flags.tested = run_internal_tests(sg, window, values, flags)

        if event == "open_tests":
            open_internal_tests()

        if event == "add_word_to_db":
            if flags.tested is False:
                window["messages"].update("test first!", text_color="red")
            else:
                last_button = display_summary(values, window, sg)
                if last_button == "ok_button":
                    success = add_word_to_db(window, values)
                    if success:
                        clear_errors(window)
                        clear_values(values, window)
                        get_next_ids(window)
                        reset_flags(flags)

        if event == "update_word":
            if flags.tested is False:
                window["messages"].update("test first!", text_color="red")
            else:
                last_button = display_summary(values, window, sg)
                if last_button == "ok_button":
                    success = update_word_in_db(window, values)
                    if success:
                        clear_errors(window)
                        clear_values(values, window)
                        get_next_ids(window)
                        reset_flags(flags)

        if event == "Debug":
            print(f"{values}")

        if event == sg.WIN_CLOSED:
            break

        if event == "Close":
            window["messages"].update(
                "backing up db to csvs", text_color="white")
            backup_db_to_tsvs()
            # export_anki_csvs()
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

        # background colour logic
        if event == "show_fields_all":
            for value in values:
                window[value].update(visible=True)
                window["bold_cc_button"].update(visible=True)
                window["bold_2_button"].update(visible=True)

        if event == "show_fields_root":
            hide_list = [
                "meaning_2", "family_word", "family_compound", "compound_type",
                "compound_construction", "bold_cc", "bold_cc_button",
                "bold_2", "bold_2_button",
                "another_eg_2",
                "source_2", "sutta_2",
                "example_2"
            ]
            for value in values:
                window[value].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)

        if event == "show_fields_compound":
            hide_list = [
                "verb", "trans", "meaning_2", "root_key", "family_root",
                "root_sign",  "root_base", "family_word", "derivative",
                "suffix", "non_root_in_comps", "non_ia", "source_2", "sutta_2",
                "example_2", "bold_2", "bold_2_button", "another_eg_2",
                ]
            for value in values:
                window[value].update(visible=True)
                window["bold_cc_button"].update(visible=True)
                window["bold_2_button"].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)

        if event == "show_fields_neither":
            hide_list = [
                "verb", "trans", "meaning_2", "root_key", "family_root",
                "root_sign",  "root_base", "family_compound",
                "compound_type", "compound_construction", "bold_cc",
                "bold_cc_button",
                "non_root_in_comps", "source_2", "sutta_2",
                "example_2", "bold_2", "bold_2_button", "another_eg_2",
                ]
            for value in values:
                window[value].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)

        if event == "stash":
            with open(pth.stash_path, "wb") as f:
                pickle.dump(values, f)

        if event == "unstash":
            with open(pth.stash_path, "rb") as f:
                unstash = pickle.load(f)
                for key, value in unstash.items():
                    window[key].update(value)

        if event == "summary":
            display_summary(values, window, sg)

    window.close()


if __name__ == "__main__":
    main()
