#!/usr/bin/env python3

import PySimpleGUI as sg
import re
import pandas as pd
import pickle
import pyperclip

from copy import deepcopy
from rich import print

from window_layout import window_layout
from functions_db import udpate_word_in_db
from functions_db import get_next_ids
from functions_db import get_family_root_values
from functions_db import get_root_sign_values
from functions_db import get_root_base_values
from functions_db import get_synonyms
from functions_db import get_sanskrit
from functions_db import copy_word_from_db
from functions_db import edit_word_in_db
from functions_db import get_pali_clean_list
from functions_db import delete_word
from functions_db import get_root_info
from functions_db import fetch_id_or_pali
from functions_db import fetch_ru
from functions_db import fetch_sbs
from functions_db import dps_update_db

from functions import open_in_goldendict
from functions import sandhi_ok
from functions import test_book_to_add
from functions import make_words_to_add_list
from functions import add_sandhi_rule, open_sandhi_rules
from functions import add_sandhi_correction
from functions import open_sandhi_corrections
from functions import add_spelling_mistake
from functions import open_spelling_mistakes
from functions import add_variant_reading
from functions import open_variant_readings
from functions import open_sandhi_exceptions
from functions import open_sandhi_ok
from functions import open_inflection_tables
from functions import find_sutta_example
from functions import find_commentary_defintions
from functions import check_spelling
from functions import add_spelling
from functions import edit_spelling
from functions import clear_errors
from functions import clear_values
from functions import add_stem_pattern
from functions import Flags, reset_flags
from functions import display_summary
from functions import test_family_compound
from functions import remove_word_to_add
from functions import add_to_word_to_add
from functions import save_gui_state
from functions import load_gui_state
from functions import test_construction
from functions import replace_sandhi
from functions import test_username
from functions import populate_dps_tab
from functions import update_sbs_chant
from functions import clear_dps
from functions import compare_differences

from functions_tests import individual_internal_tests
from functions_tests import open_internal_tests
from functions_tests import db_internal_tests

from db.get_db_session import get_db_session
from scripts.db_to_tsv import db_to_tsv

from tools.pos import DECLENSIONS, VERBS
from tools.pos import POS
from tools.sandhi_contraction import make_sandhi_contraction_dict
from tools.paths import ProjectPaths as PTH


def main():
    db_session = get_db_session("dpd.db")
    primary_user = test_username(sg)
    pali_word_original = None

    # !!! this is slow !!!
    try:
        definitions_df = pd.read_csv(PTH.defintions_csv_path, sep="\t")
    except Exception:
        definitions_df = pd.DataFrame()

    sandhi_dict = make_sandhi_contraction_dict(db_session)
    pali_clean_list: list = get_pali_clean_list()
    window = window_layout()

    flags = Flags()
    get_next_ids(window)

    # load the previously saved state of the gui
    try:
        saved_values, words_to_add_list = load_gui_state()
        for key, value in saved_values.items():
            window[key].update(value)
        window["word_to_add"].update(words_to_add_list)
        window["words_to_add_length"].update(len(words_to_add_list))
    except FileNotFoundError:
        window["messages"].update(
            "previously saved state not found. select a book to add",
            text_color="white")
        words_to_add_list = []

    while True:
        event, values = window.read()

        if event:
            print(f"{event}")
            # print(f"{values}")

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

        # add book
        elif event == "book_to_add_enter" or event == "books_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = make_words_to_add_list(
                    window, values["book_to_add"])

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(words_to_add_list)
                    window["words_to_add_length"].update(
                        len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        f"added all missing words from {values['book_to_add']}",
                        text_color="white")
                else:
                    window["messages"].update(
                        "empty list, try again", text_color="red")

        # open word in goldendict

        elif event == "word_to_add":
            if values["word_to_add"] != []:
                open_in_goldendict(values["word_to_add"][0])
                pyperclip.copy(values["word_to_add"][0])
                print(window["word_to_add"].get_list_values())

        # sandhi ok

        elif event == "sandhi_ok":
            print(values)
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                sandhi_ok(window, values["word_to_add"][0])

                if values["word_to_add"][0] in words_to_add_list:
                    words_to_add_list.remove(values["word_to_add"][0])

                try:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(words_to_add_list)
                    window["words_to_add_length"].update(
                        len(words_to_add_list))
                    open_in_goldendict(words_to_add_list[0])
                except IndexError:
                    window["messages"].update(
                        "no more words to add", text_color="red")

        # add word

        elif event == "add_word":
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(len(words_to_add_list))
                window["tab_edit_dpd"].select()
                window["pali_1"].update(values["word_to_add"][0])
                window["search_for"].update(values["word_to_add"][0])
                window["bold_1"].update(values["word_to_add"][0])
                window["messages"].update("adding word", text_color="white")
                window["pali_1"].set_focus(force=True)

        # fix sandhi

        elif event == "fix_sandhi":
            if values["word_to_add"] == []:
                window["messages"].update("nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(len(words_to_add_list))
                window["tab_fix_sandhi"].select()
                window["example"].update(values["word_to_add"][0])
                window["sandhi_to_correct"].update(values["word_to_add"][0])
                window["spelling_mistake"].update(values["word_to_add"][0])
                window["variant_reading"].update(values["word_to_add"][0])

        elif event == "update_inflection_templates":
            open_inflection_tables()

        elif event == "remove_word":
            words_to_add_list = remove_word_to_add(
                values, window, words_to_add_list)
            window["words_to_add_length"].update(len(words_to_add_list))

        # add word events

        elif event == "pali_2":
            if flags.pali_2:
                window["pali_2"].update(f"{values['pali_1']}")
                flags.pali_2 = False

        # test pos
        elif event == "grammar":
            if values["pos"] not in POS:
                window["pos_error"].update(
                    f"'{values['pos']}' not a valid pos", text_color="red")

        if event == "grammar":
            if flags.grammar and values["grammar"] == "":
                if values["pos"] in VERBS:
                    window["grammar"].update(f"{values['pos']} of ")
                else:
                    window["grammar"].update(f"{values['pos']}, ")
                flags.grammar = False

        if event == "derived_from":
            if flags.derived_from:
                if (
                    " of " in values["grammar"] or
                    " from " in values["grammar"]
                ):
                    derived_from = re.sub(
                        ".+( of | from )(.+)(,|$)", r"\2", values["grammar"])
                    derived_from = re.sub("^na ", "", derived_from)
                    window["derived_from"].update(derived_from)
                    flags.derived_from = False

            # hide irrelevant fields
            if flags.show_fields:
                if re.findall(r"\bcomp\b", values["grammar"]) != []:
                    event = "show_fields_compound"
                    flags.show_fields = True
                else:
                    event = "show_fields_root"
                    flags.show_fields = True

        # movement in this field triggers a spellcheck
        elif event == "add_spelling":
            field = "meaning_1"
            error_field = "meaning_1_error"
            check_spelling(field, error_field, values, window)

        elif event == "check_spelling_button":
            field = "meaning_1"
            error_field = "meaning_1_error"
            check_spelling(field, error_field, values, window)

            field = "meaning_lit"
            error_field = "meaning_lit_error"
            check_spelling(field, error_field, values, window)

            field = "meaning_2"
            error_field = "meaning_2_error"
            check_spelling(field, error_field, values, window)

        elif event == "add_spelling_button":
            word = values["add_spelling"]
            add_spelling(word)
            window["messages"].update(
                f"{word} added to dictionary", text_color="white")

        elif event == "edit_spelling_button":
            edit_spelling()

        elif event == "family_root":
            root_info = get_root_info(values["root_key"])
            window["root_info"].update(root_info)

        elif (
                event == "family_root" and
                values["family_root"] == ""
                and values["root_key"] != ""
        ):
            if flags.family_root:
                root_key = values["root_key"]
                try:
                    FAMILY_ROOT_VALUES = get_family_root_values(root_key)
                    window["family_root"].update(values=FAMILY_ROOT_VALUES)
                    flags.family_root = False
                except UnboundLocalError as e:
                    window["messages"].update(
                        f"not a root. {e}", text_color="red")

        elif event == "get_family_root":
            if values["root_key"] != "":
                root_key = values["root_key"]
                FAMILY_ROOT_VALUES = get_family_root_values(root_key)
                window["family_root"].update(values=FAMILY_ROOT_VALUES)
                flags.family_root = False
            else:
                window["messages"].update(
                    "no root_key selected", text_color="red")

        elif event == "root_sign" and values["root_sign"] == "":
            if flags.root_sign:
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                flags.root_sign = False

        elif event == "get_root_sign":
            if values["root_key"] != "":
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                flags.root_sign = False
            else:
                window["messages"].update(
                    "no root_key selected", text_color="red")

        elif event == "root_base" and values["root_base"] == "":
            if flags.root_base:
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                flags.root_base = False

        elif event == "get_root_base":
            if values["root_key"] != "":
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                flags.root_base = False
            else:
                window["messages"].update(
                    "no root_key selected", text_color="red")

        elif event == "family_compound":
            if (
                flags.family_compound and
                values["family_compound"] == "" and
                values["root_key"] == ""
            ):
                window["family_compound"].update(values["pali_1"])
                flags.family_compound = False
            else:
                test_family_compound(values, window)

        elif event == "construction":
            if flags.construction and values["construction"] == "":
                # build a construction from root family and base
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

                # if compound update with pali_1
                elif re.findall(r"\bcomp\b", values["grammar"]) != []:
                    window["construction"].update(values["pali_1"])

                flags.construction = False

            # test construciton for missing headwords
            if values["root_key"] == "":
                test_construction(values, window, pali_clean_list)

        elif (event == "add_construction_enter" or
                event == "add_construction_button"):
            words_to_add_list = add_to_word_to_add(
                values, window, words_to_add_list)
            window["word_to_add"].update(words_to_add_list)
            window["words_to_add_length"].update(len(words_to_add_list))

        elif event == "derivative":
            print("hello")
            "ptp" in values["grammar"]
            if "ptp" in values["grammar"]:
                window["derivative"].update("kicca")

        elif event == "suffix":
            if flags.suffix and values["pos"] in DECLENSIONS:
                if "comp" not in values["grammar"]:
                    suffix = values["construction"]
                    suffix = re.sub(r"\n.+", "", suffix)
                    suffix = re.sub(r".+ \+ ", "", suffix)
                    window["suffix"].update(suffix)
                flags.suffix = False

        elif event == "compound_construction":
            if (
                values["compound_type"] != "" and
                flags.compound_construction and
                values["compound_construction"] == ""
            ):
                if values["root_key"]:
                    window["compound_construction"].update(
                        values["pali_1"])
                    flags.compound_construction = False
                else:
                    window["compound_construction"].update(
                        values["construction"])
                    flags.compound_construction = False

        elif event == "bold_cc_button" or event == "bold_cc_enter":
            cc_bold = re.sub(
                values["bold_cc"],
                f"<b>{values['bold_cc']}</b>",
                values["compound_construction"])
            window["compound_construction"].update(cc_bold)
            window["bold_cc"].update("")

        elif (
            (
                event == "example_1"
                and flags.example_1 and
                values["example_1"] == "" and
                values["pali_1"] and
                values["word_to_add"]
            ) or
            (
                event == "source_1" and
                flags.example_1 and
                values["example_1"] == "" and
                values["pali_1"] and
                values["word_to_add"]
            ) or
            (
                event == "sutta_1" and
                flags.example_1 and
                values["example_1"] == "" and
                values["pali_1"] and
                values["word_to_add"]
            ) or
            event == "another_eg_1"
        ):

            if values["book_to_add"] == "":
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add
                    window["book_to_add"].update(book_to_add)

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["pali_1"][:-1],
                    title=None,
                    location=(400, 400))
                if word_to_add:
                    values["word_to_add"] = [word_to_add]
                    window["word_to_add"].update([word_to_add])

            if (
                test_book_to_add(values, window) and
                values["book_to_add"] and
                values["word_to_add"]
            ):
                sutta_sentences = find_sutta_example(sg, window, values)

                if sutta_sentences is not None:
                    try:
                        window["source_1"].update(sutta_sentences["source"])
                        window["sutta_1"].update(sutta_sentences["sutta"])
                        window["example_1"].update(sutta_sentences["example"])
                    except KeyError as e:
                        window["messages"].update(e, text_color="red")

                flags.example_1 = False

        elif event == "bold_1_button" or event == "bold_1_enter":
            # bold
            example_1_bold = re.sub(
                values["bold_1"],
                f"<b>{values['bold_1']}</b>",
                values["example_1"])
            window["example_1"].update(example_1_bold)
            window["bold_1"].update("")

        elif event == "example_1_lower":
            values["example_1"] = values["example_1"].lower()
            window["example_1"].update(values["example_1"])

        elif event == "example_1_clean":
            replace_sandhi(
                values["example_1"], "example_1", sandhi_dict, window)
            replace_sandhi(
                values["bold_1"], "bold_1", sandhi_dict, window)

        elif event == "example_2_clean":
            replace_sandhi(
                values["example_2"], "example_2", sandhi_dict, window)
            replace_sandhi(
                values["bold_2"], "bold_2", sandhi_dict, window)

        elif event == "commentary_clean":
            replace_sandhi(
                values["commentary"], "commentary", sandhi_dict, window)

        elif event == "another_eg_2":
            if values["book_to_add"] == "":
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                values["book_to_add"] = book_to_add
                window["book_to_add"].update(book_to_add)

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["pali_1"],
                    title=None,
                    location=(400, 400))
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update([word_to_add])

            sutta_sentences = find_sutta_example(sg, window, values)

            if sutta_sentences is not None:
                try:
                    window["source_2"].update(sutta_sentences["source"])
                    window["sutta_2"].update(sutta_sentences["sutta"])
                    window["example_2"].update(sutta_sentences["example"])
                except KeyError as e:
                    window["messages"].update(e, text_color="red")

            flags.example_2 = False

        elif event == "bold_2_button" or event == "bold_2_enter":
            # bold
            example_2_bold = re.sub(
                values["bold_2"],
                f"<b>{values['bold_2']}</b>",
                values["example_2"])
            window["example_2"].update(example_2_bold)
            window["bold_2"].update("")

        elif event == "example_2_lower":
            values["example_2"] = values["example_2"].lower()
            window["example_2"].update(values["example_2"])

        elif event == "synonym":
            if flags.synoyms:
                synoyms = get_synonyms(values["pos"], values["meaning_1"])
                window["synonym"].update(synoyms)
                flags.synoyms = False

        elif event == "search_for":
            if values["search_for"] == "":
                window["search_for"].update(values["pali_1"])

        elif (
            event == "search_for_enter" or
            event == "defintions_search_button"
        ):
            try:
                commentary_defintions = find_commentary_defintions(
                    sg, values, definitions_df)
            except NameError as e:
                window["messages"].update(
                    f"turn on the definitions db! {e}", text_color="red")

            if commentary_defintions:
                commentary = ""
                for c in commentary_defintions:
                    commentary += f"({c['ref_code']}) {c['commentary']}\n"
                commentary = commentary.rstrip("\n")
                window["commentary"].update(commentary)

        elif event == "sanskrit":
            if flags.sanskrit and re.findall(
                    r"\bcomp\b", values["grammar"]) != []:
                sanskrit = get_sanskrit(values["construction"])
                window["sanskrit"].update(sanskrit)
                flags.sanskrit = False

        elif event == "stem":
            if flags.stem:
                add_stem_pattern(values, window)
                flags.stem = False

        # add word buttons

        elif event == "Clone" or event == "word_to_clone_edit_enter":
            if values["word_to_clone_edit"] != "":
                copy_word_from_db(values, window)
                window["word_to_clone_edit"].update("")
            else:
                window["messages"].update("No word to copy!", text_color="red")

        elif event == "edit_button":
            if values["word_to_clone_edit"] != "":
                pali_word_original = edit_word_in_db(values, window)
                pali_word_original2 = deepcopy(pali_word_original)
                window["word_to_clone_edit"].update("")
            else:
                window["messages"].update("No word to edit!", text_color="red")

        elif event == "clear_button":
            clear_errors(window)
            clear_values(values, window)
            get_next_ids(window)
            reset_flags(flags)
            window["messages"].update("")

        elif event == "test_internal":

            clear_errors(window)
            flags = individual_internal_tests(sg, window, values, flags)

            # spell checks
            field = "meaning_1"
            error_field = "meaning_1_error"
            check_spelling(field, error_field, values, window)

            field = "meaning_lit"
            error_field = "meaning_lit_error"
            check_spelling(field, error_field, values, window)

            field = "meaning_2"
            error_field = "meaning_2_error"
            check_spelling(field, error_field, values, window)

        elif event == "open_tests_button":
            open_internal_tests()

        elif event == "update_sandhi_button":
            sandhi_dict = make_sandhi_contraction_dict(db_session)

        elif event == "update_db_button":
            if flags.tested is False:
                window["messages"].update("test first!", text_color="red")
            else:
                last_button = display_summary(values, window, sg)
                if last_button == "ok_button":
                    success, action = udpate_word_in_db(
                        window, values)
                    if success:
                        if not primary_user:
                            compare_differences(
                                values, sg, pali_word_original2, action)
                        clear_errors(window)
                        clear_values(values, window)
                        get_next_ids(window)
                        reset_flags(flags)
                        remove_word_to_add(values, window, words_to_add_list)
                        window["words_to_add_length"].update(
                            len(words_to_add_list))
                        if not primary_user:
                            edit_in_dps = sg.popup_ok_cancel(
                                "Edit word in DPS?", title="edit in dps",
                                location=(400, 400))
                            if edit_in_dps:
                                window["dps_id_or_pali_1"].update(values["id"])
                                window["tab_edit_dps"].select()

        elif event == "debug_button":
            print(f"{values}")

        elif event == "save_state_button":
            save_gui_state(values, words_to_add_list)

        elif event == "delete_button":
            row_id = values['id']
            pali_1 = values['pali_1']
            yes_no = sg.popup_yes_no(
                f"Are you sure you want to delete {row_id} {pali_1}?",
                location=(400, 400),
                modal=True)
            if yes_no == "Yes":
                success = delete_word(values, window)
                if success:
                    clear_errors(window)
                    clear_values(values, window)
                    get_next_ids(window)
                    reset_flags(flags)
                    window["messages"].update(
                        f"{row_id} '{pali_1}' deleted", text_color="white")

        elif event == "save_and_close_button":
            window["messages"].update(
                "backing up db to csvs", text_color="white")
            db_to_tsv()
            save_gui_state(values, words_to_add_list)
            break

        # fix sandhi events

        # sandhi rules
        elif event == "add_sandhi_rule":
            add_sandhi_rule(window, values)

        elif event == "open_sandhi_rules":
            open_sandhi_rules()

        # sandhi corrections
        elif event == "add_sandhi_correction":
            add_sandhi_correction(window, values)

        elif event == "open_sandhi_corrections":
            open_sandhi_corrections()

        # spelling mistakes
        elif event == "add_spelling_mistake":
            add_spelling_mistake(window, values)

        elif event == "open_spelling_mistakes":
            open_spelling_mistakes()

        # variant readings
        elif event == "add_variant_reading":
            add_variant_reading(window, values)

        elif event == "open_variant_readings":
            open_variant_readings()

        elif event == "open_sandhi_ok":
            open_sandhi_ok()

        elif event == "open_sandhi_exceptions":
            open_sandhi_exceptions()

        # hide fields logic

        elif event == "show_fields_all":
            for value in values:
                window[value].update(visible=True)
                window["get_family_root"].update(visible=True)
                window["get_root_base"].update(visible=True)
                window["get_root_sign"].update(visible=True)
                window["bold_cc_button"].update(visible=True)
                window["bold_2_button"].update(visible=True)
                window["another_eg_2"].update(visible=True)
                window["example_2_lower"].update(visible=True)
                flags.show_fields = False

        elif event == "show_fields_root":
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
            window["get_family_root"].update(visible=True)
            window["get_root_base"].update(visible=True)
            window["get_root_sign"].update(visible=True)
            flags.show_fields = False

        elif event == "show_fields_compound":
            hide_list = [
                "verb", "trans", "meaning_2", "root_key", "family_root",
                "get_family_root", "root_sign",  "get_root_sign", "root_base",
                "get_root_base", "family_word", "derivative",
                "suffix", "non_root_in_comps", "non_ia", "source_2", "sutta_2",
                "example_2", "bold_2", "bold_2_button", "example_2_lower",
                "another_eg_2",
                ]
            for value in values:
                window[value].update(visible=True)
                window["bold_cc_button"].update(visible=True)
                window["bold_2_button"].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)
            flags.show_fields = False

        elif event == "show_fields_word":
            hide_list = [
                "verb", "trans", "meaning_2", "root_key",
                "family_root", "get_family_root",
                "root_sign",  "get_root_sign",
                "root_base", "get_root_base",
                "family_compound",
                "compound_type", "compound_construction",
                "bold_cc", "bold_cc_button",
                "non_root_in_comps",
                "source_2", "sutta_2", "example_2",
                "bold_2", "bold_2_button",  "example_2_lower", "another_eg_2",
                ]
            for value in values:
                window[value].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)
            flags.show_fields = False

        elif event == "stash_button":
            with open(PTH.stash_path, "wb") as f:
                pickle.dump(values, f)
            window["messages"].update(
                f"{values['pali_1']} stashed", text_color="white")

        elif event == "unstash_button":
            with open(PTH.stash_path, "rb") as f:
                unstash = pickle.load(f)
                for key, value in unstash.items():
                    window[key].update(value)

            window["messages"].update(
                "unstashed", text_color="white")

        elif event == "summary_button":
            display_summary(values, window, sg)

        elif event == "test_db_internal":
            db_internal_tests(sg, window, flags)

        elif event == "test_next":
            flags.test_next = True

        elif event == "test_edit":
            open_internal_tests()

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

        # dps tab

        # tabs jumps to next field in multiline
        if event == "dps_ru_meaning_tab":
            window['dps_ru_meaning'].get_next_focus().set_focus()
        elif event == "dps_sbs_meaning_tab":
            window['dps_sbs_meaning'].get_next_focus().set_focus()
        elif event == "dps_notes_tab":
            window['dps_notes'].get_next_focus().set_focus()
        elif event == "dps_ru_notes_tab":
            window['dps_ru_notes'].get_next_focus().set_focus()
        elif event == "dps_sbs_notes_tab":
            window['dps_sbs_notes'].get_next_focus().set_focus()
        elif event == "dps_example_1_tab":
            window['dps_example_1'].get_next_focus().set_focus()
        elif event == "dps_example_2_tab":
            window['dps_example_2'].get_next_focus().set_focus()
        elif event == "dps_sbs_example_3_tab":
            window['dps_sbs_example_3'].get_next_focus().set_focus()
        elif event == "dps_sbs_example_4_tab":
            window['dps_sbs_example_4'].get_next_focus().set_focus()

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
