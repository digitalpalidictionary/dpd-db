#!/usr/bin/env python3

"""Main program to run the GUI."""

import json
import subprocess
import PySimpleGUI as sg
import re
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
from functions_db import get_lemma_clean_list
from functions_db import delete_word
from functions_db import get_root_info
from functions_db import fetch_id_or_lemma_1
from functions_db import get_family_compound_values
from functions_db import get_family_idioms_values
from functions_db import del_syns_if_pos_meaning_changed

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
from functions import test_family_idioms
from functions import remove_word_to_add
from functions import add_to_word_to_add
from functions import save_gui_state
from functions import load_gui_state
from functions import test_construction
from functions import replace_sandhi
from functions import test_username
from functions import compare_differences
from functions import stasher, unstasher
from functions import increment_lemma_1
from functions import make_compound_construction
from functions import make_construction
from functions import make_lemma_clean
from functions import make_has_values_list

from functions_tests import individual_internal_tests
from functions_tests import open_internal_tests
from functions_tests import db_internal_tests

from functions_daily_record import daily_record_update

from functions_dps import fetch_ru
from functions_dps import fetch_sbs
from functions_dps import dps_update_db
from functions_dps import dps_get_synonyms
from functions_dps import dps_make_words_to_add_list
from functions_dps import dps_make_words_to_add_list_sutta
from functions_dps import dps_make_words_to_add_list_from_text
from functions_dps import dps_make_words_to_add_list_from_text_filtered
from functions_dps import dps_make_words_to_add_list_from_text_no_field
from functions_dps import fetch_matching_words_from_db_with_conditions
from functions_dps import fetch_matching_words_from_db
from functions_dps import words_in_db_with_value_in_field_sbs
from functions_dps import populate_dps_tab
from functions_dps import update_sbs_chant
from functions_dps import clear_dps
from functions_dps import translate_to_russian_googletrans
from functions_dps import ru_translate_with_openai
from functions_dps import en_translate_with_openai
from functions_dps import ru_notes_translate_with_openai
from functions_dps import swap_sbs_examples
from functions_dps import remove_sbs_example
from functions_dps import copy_dpd_examples
from functions_dps import display_dps_summary
from functions_dps import copy_and_split_content
from functions_dps import ru_check_spelling
from functions_dps import ru_add_spelling
from functions_dps import ru_edit_spelling
from functions_dps import Flags_dps, dps_reset_flags
from functions_dps import edit_corrections
from functions_dps import tail_log
from functions_dps import stash_values_from
from functions_dps import unstash_values_to
from functions_dps import dps_get_original_values
from functions_dps import update_field
from functions_dps import update_field_with_change
from functions_dps import words_in_db_from_source
from functions_dps import get_next_ids_dps
from functions_dps import add_number_to_pali
from functions_dps import read_tsv_words
from functions_dps import save_gui_state_dps
from functions_dps import load_gui_state_dps
from functions_dps import send_sutta_study_request

from functions_tests_dps import dps_open_internal_tests
from functions_tests_dps import dps_individual_internal_tests
from functions_tests_dps import dps_db_internal_tests
from functions_tests_dps import check_repetition
from functions_tests_dps import dps_dpd_db_internal_tests

from pass2 import pass2_gui, Pass2Data
from pass2 import start_from_where_gui

from db.get_db_session import get_db_session
from scripts.backup_dpd_headwords_and_roots import backup_dpd_headwords_and_roots
from scripts.backup_ru_sbs import backup_ru_sbs

from tools.i2html import make_html
from tests.test_allowable_characters import test_allowable_characters_gui
from tests.test_allowable_characters import test_allowable_characters_gui_dps

from tools.goldedict_tools import open_in_goldendict
from tools.paths import ProjectPaths
from tools.pos import DECLENSIONS, VERBS
from tools.pos import POS
from tools.sandhi_contraction import make_sandhi_contraction_dict

from dps.tools.paths_dps import DPSPaths


def main():
    pth: ProjectPaths = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    username = test_username(sg)
    pali_word_original = None
    pali_word_original2 = None
    
    family_compound_values = get_family_compound_values(db_session)
    family_idioms_values = get_family_idioms_values(db_session)
    sandhi_dict = make_sandhi_contraction_dict(db_session)

    with open(pth.hyphenations_dict_path) as f:
        hyphenations_dict = json.load(f)

    lemma_clean_list: list = get_lemma_clean_list(db_session)
    window = window_layout(dpspth, db_session, username)
    daily_record_update(window, pth, "refresh", 0)

    # load the previously saved state of the gui
    try:
        saved_values, words_to_add_list = load_gui_state(pth)
        for key, value in saved_values.items():
            window[key].update(value)
        window["word_to_add"].update(words_to_add_list)
        window["words_to_add_length"].update(value=len(words_to_add_list))
    except FileNotFoundError:
        window["messages"].update(value="previously saved state not found. select a book to add",
            text_color="white")
        words_to_add_list = []

    flags: Flags = Flags()
    dps_flags = Flags_dps()
    if username == "primary_user":
        get_next_ids(db_session, window)
    elif username == "deva":
        get_next_ids_dps(db_session, window)
    else:
    # Perform actions for other usernames
        get_next_ids(db_session, window)
    

    hide_list_all = [
        "sutta_to_add", "source_to_add", "field_for_id_list", "online_suggestion"
    ]

    while True:
        event, values = window.read() # type: ignore

        if event:
            print(f"{event}")
            # print(f"{values}")

        if event == sg.WIN_CLOSED:
            break

        elif event == "control_q":
            close_yes_cancel = sg.popup_ok_cancel(
                    "Are you sure you want to quit?",
                    title="Quit",
                    location=(400, 400))
            if close_yes_cancel == "OK":
                break

        # tabs jumps to next field in multiline
        if event == "meaning_1_tab":
            focus = window['meaning_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "construction_tab":
            focus = window['construction'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "phonetic_tab":
            focus = window['phonetic'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "commentary_tab":
            focus = window['commentary'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "notes_tab":
            focus = window['notes'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "notes_italic_bold_tab":
            focus = window['notes_italic_bold'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_1_tab":
            focus = window['example_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_2_tab":
            focus = window['example_2'].get_next_focus()
            if focus is not None:
                focus.set_focus()

        # word to add tab
        # add book
        elif event == "book_to_add_enter" or event == "books_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = make_words_to_add_list(
                    db_session, pth, window, values["book_to_add"])

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        value=f"added missing words from {values['book_to_add']}",
                        text_color="white")
                else:
                    window["messages"].update(
                        value="empty list, try again", text_color="red")

        # open word in goldendict

        elif event == "word_to_add":
            if values["word_to_add"] != []:
                open_in_goldendict(values["word_to_add"][0])
                pyperclip.copy(values["word_to_add"][0])
                print(window["word_to_add"].get_list_values()) # type: ignore

        # sandhi ok

        elif event == "sandhi_ok":
            print(values)
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                sandhi_ok(pth, window, values["word_to_add"][0])
                daily_record_update(window, pth, "check", values["word_to_add"][0])

                if values["word_to_add"][0] in words_to_add_list:
                    words_to_add_list.remove(values["word_to_add"][0])

                try:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))
                    open_in_goldendict(words_to_add_list[0])
                except IndexError:
                    window["messages"].update(
                        value="no more words to add", text_color="red")

        # add word

        elif event == "add_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                window["tab_edit_dpd"].select()  # type: ignore
                window["lemma_1"].update(values["word_to_add"][0])
                window["search_for"].update(values["word_to_add"][0][:-1])
                window["bold_1"].update(values["word_to_add"][0])
                window["messages"].update(value="adding word", text_color="white")
                window["lemma_1"].set_focus(force=True)

        # fix sandhi

        elif event == "fix_sandhi":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                daily_record_update(window, pth, "check", values["word_to_add"][0])
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                window["tab_fix_sandhi"].select()  # type: ignore
                window["example"].update(values["word_to_add"][0])
                window["sandhi_to_correct"].update(values["word_to_add"][0])
                window["spelling_mistake"].update(values["word_to_add"][0])
                window["variant_reading"].update(values["word_to_add"][0])

        elif event == "update_inflection_templates":
            open_inflection_tables(pth)

        elif event == "remove_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                daily_record_update(window, pth, "check", values["word_to_add"][0])
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
        
        # pass2
        elif (
            event == "pass2_button"
            or event == "pass2_button0"
            or event == "control_p"
        ):
            if flags.pass2_start:
                book = values["book_to_add"]
                window["messages"].update(
                    value="loading pass2 data...", text_color="white")
                p2d = Pass2Data(pth, db_session, window, values, book)
                start_from_where_gui(p2d)
                flags.pass2_start = False
                p2d, wd = pass2_gui(p2d)
            else:
                p2d.db_session = db_session
                p2d, wd = pass2_gui(p2d)


        # DPD edit tab

        # tabs jumps to next field in multiline
        if event == "lemma_1_tab":
            focus = window['lemma_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()        
        elif event == "lemma_2_tab":
            focus = window['lemma_2'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "pos_tab":
            focus = window['pos'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "grammar_tab":
            focus = window['grammar'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "meaning_1_tab":
            focus = window['meaning_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "construction_tab":
            focus = window['construction'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "phonetic_tab":
            focus = window['phonetic'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "commentary_tab":
            focus = window['commentary'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_1_tab":
            focus = window['example_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_2_tab":
            focus = window['example_2'].get_next_focus()
            if focus is not None:
                focus.set_focus()

        # add word events
        
        if event == "get_next_id_button":
            get_next_ids(db_session, window)

        # copy lemma_1 to lemma_2
        if event == "lemma_1_tab":
            if flags.lemma_2:
                lemma_2 = re.sub(" \\d.*", "", values['lemma_1'])
                window["lemma_2"].update(value=lemma_2)
                flags.lemma_2 = False

        # test pos
        if event == "grammar":
            if (
                values["pos"] not in POS and
                values["lemma_1"]
            ):
                window["pos_error"].update(
                    value=f"'{values['pos']}' not a valid pos", text_color="red")

            # add pos to grammar
            if flags.grammar and not values["grammar"]:
                if values["pos"] in VERBS:
                    window["grammar"].update(value=f"{values['pos']} of ")
                else:
                    window["grammar"].update(value=f"{values['pos']}, ")
                flags.grammar = False
        
        # lemma_2 masc o / nt aṃ / masc as
        if event == "pos_tab":
            if (
                values["pos"] == "masc" and
                values["lemma_2"].endswith("a")
            ):
                masc_o = re.sub("a$", "o", values["lemma_2"])
                window["lemma_2"].update(value=masc_o)
            elif (
                values["pos"] == "nt" and
                values["lemma_2"].endswith("a")
            ):
                nt_aṃ = re.sub("a$", "aṃ", values["lemma_2"])
                window["lemma_2"].update(value=nt_aṃ)
            elif (
                values["pos"] == "masc" and
                values["lemma_2"].endswith("as")
            ):
                masc_as = re.sub("as$", "ā", values["lemma_2"])
                window["lemma_2"].update(value=masc_as)
                window["grammar"].update(value="masc, mano group, ")
            # fix adjecitves ending with 'o' and 'aṃ'
            elif (
                values["pos"] == "adj"
                and (
                    values["lemma_2"].endswith("aṃ")
                    or values["lemma_2"].endswith("o"))
            ):
                a_adj = re.sub("(aṃ|o)$", "a", values["lemma_2"])
                window["lemma_2"].update(value=a_adj)

        if event == "derived_from":
            if flags.derived_from:
                if (
                    " of " in values["grammar"] or
                    " from " in values["grammar"]
                ):
                    derived_from = re.sub(
                        ".+( of | from )(.+)(,|$)", r"\2", values["grammar"])
                    derived_from = re.sub("^na ", "", derived_from)
                    window["derived_from"].update(value=derived_from)
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

        elif event == "check_spelling_button":
            field = "meaning_1"
            error_field = "meaning_1_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            field = "meaning_lit"
            error_field = "meaning_lit_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            field = "meaning_2"
            error_field = "meaning_2_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

        elif event == "add_spelling_button":
            word = values["add_spelling"]
            add_spelling(pth, word)
            window["messages"].update(
                value=f"{word} added to dictionary", text_color="white")
            window["add_spelling"].update(value="")

        elif event == "edit_spelling_button":
            edit_spelling(pth)

        elif event == "family_root":
            root_info = get_root_info(db_session, values["root_key"])
            window["root_info"].update(value=root_info)

        elif (
                event == "family_root" and
                not values["family_root"] and
                values["root_key"]
        ):
            if flags.family_root:
                root_key = values["root_key"]
                try:
                    FAMILY_ROOT_VALUES = get_family_root_values(db_session, root_key)
                    window["family_root"].update(values=FAMILY_ROOT_VALUES)
                    flags.family_root = False
                except UnboundLocalError as e:
                    window["messages"].update(
                        value=f"not a root. {e}", text_color="red")

        elif event == "get_family_root":
            if values["root_key"]:
                root_key = values["root_key"]
                FAMILY_ROOT_VALUES = get_family_root_values(db_session, root_key)
                window["family_root"].update(values=FAMILY_ROOT_VALUES)
                flags.family_root = False

                # get root_sign and root_base if they are empty
                if not values["root_sign"]:
                    ROOT_SIGN_VALUES = get_root_sign_values(db_session, root_key)
                    window["root_sign"].update(values=ROOT_SIGN_VALUES)
                    flags.root_sign = False
                if not values["root_base"]:
                    ROOT_BASE_VALUES = get_root_base_values(db_session, root_key)
                    window["root_base"].update(values=ROOT_BASE_VALUES)
                    flags.root_base = False

            else:
                window["messages"].update(
                    value="no root_key selected", text_color="red")

        elif event == "root_sign" and not values["root_sign"]:
            if flags.root_sign:
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(db_session, root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                flags.root_sign = False

        elif event == "get_root_sign":
            if values["root_key"]:
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(db_session, root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                flags.root_sign = False
            else:
                window["messages"].update(
                    value="no root_key selected", text_color="red")

        elif event == "root_base" and not values["root_base"]:
            if flags.root_base:
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(db_session, root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                flags.root_base = False

        elif event == "get_root_base":
            if values["root_key"]:
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(db_session, root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                flags.root_base = False
            else:
                window["messages"].update(
                    value="no root_key selected", text_color="red")

        elif event == "family_compound":
            if (
                flags.family_compound and
                not values["family_compound"] and
                not values["root_key"]
            ):
                window["family_compound"].update(values["lemma_1"])
                flags.family_compound = False
            else:
                test_family_compound(values, window, family_compound_values)

        elif event == "family_idioms":
            if (
                flags.family_idioms and
                not values["family_idioms"] and
                not values["root_key"]
            ):
                window["family_idioms"].update(values["lemma_1"])
                flags.family_idioms = False
            else:
                test_family_idioms(values, window, family_idioms_values)

        elif event == "construction":
            if flags.construction and not values["construction"]:
                construction = make_construction(values)
                window["construction"].update(value=construction)
                flags.construction = False

            # test construciton for missing headwords
            if not values["root_key"]:
                test_construction(values, window, lemma_clean_list)

        # auto-add construction_line2
        if event == "construction_enter":
            if flags.construction_line2:
                lemma_clean = make_lemma_clean(values)
                window["construction"].update(
                    value=f"{values['construction']}\n{lemma_clean}")
                flags.construction_line2 = False

        elif (
            event == "add_construction_enter" or
            event == "add_construction_button"
        ):  
            new_word_to_add = values["add_construction"]
            words_to_add_list = add_to_word_to_add(
                words_to_add_list, new_word_to_add, window)
            window["word_to_add"].update(values=words_to_add_list)
            window["words_to_add_length"].update(value=len(words_to_add_list))

        elif event == "control_a":
            new_word_to_add = sg.popup_get_text(
                "What word would you like to add?", title="Add a word", location=(400, 400))
            if new_word_to_add:
                words_to_add_list = add_to_word_to_add(words_to_add_list, new_word_to_add, window)
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))

        elif event == "derivative":
            print("hello")
            if "ptp" in values["grammar"]:
                window["derivative"].update(value="kicca")

        elif event == "suffix":
            if flags.suffix and values["pos"] in DECLENSIONS:
                if "comp" not in values["grammar"]:
                    suffix = values["construction"]
                    suffix = re.sub(r"\n.+", "", suffix)
                    suffix = re.sub(r".+ \+ ", "", suffix)
                    window["suffix"].update(value=suffix)
                flags.suffix = False

        elif event == "compound_construction":
            if (
                values["compound_type"] and
                flags.compound_construction and
                not values["compound_construction"]
            ):
                cc = make_compound_construction(values)
                window["compound_construction"].update(value=cc)
                flags.compound_construction = False


        elif event == "bold_cc_button" or event == "bold_cc_enter":
            if values["bold_cc"]:
                cc_bold = re.sub(
                    values["bold_cc"],
                    f"<b>{values['bold_cc']}</b>",
                    values["compound_construction"])
                window["compound_construction"].update(value=cc_bold)
                window["bold_cc"].update(value="")

        elif (
            (
                event == "example_1"
                and flags.example_1 and
                not values["example_1"] and
                values["lemma_1"] and
                values["word_to_add"]
            ) or
            (
                event == "source_1" and
                flags.example_1 and
                not values["example_1"] and
                values["lemma_1"] and
                values["word_to_add"]
            ) or
            (
                event == "sutta_1" and
                flags.example_1 and
                not values["example_1"] and
                values["lemma_1"] and
                values["word_to_add"]
            ) or
            event == "another_eg_1"
        ):

            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                default_text = re.sub(r" \d.*$", "", values["lemma_1"])
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=default_text[:-1],
                    title=None,
                    location=(400, 400))
                if word_to_add:
                    values["word_to_add"] = [word_to_add]
                    window["word_to_add"].update(values=[word_to_add])

            if (
                test_book_to_add(values, window) and
                values["book_to_add"] and
                values["word_to_add"]
            ):
                source_sutta_example = find_sutta_example(pth, sg, window, values)

                if source_sutta_example is not None:
                    try:
                        window["source_1"].update(value=source_sutta_example[0])
                        window["sutta_1"].update(value=source_sutta_example[1])
                        window["example_1"].update(value=source_sutta_example[2])
                    except KeyError as e:
                        window["messages"].update(value=str(e), text_color="red")

                flags.example_1 = False

        # bold
        elif event == "bold_1_button" or event == "bold_1_enter":
            if values["bold_1"]:
                example_1_bold = re.sub(
                    values["bold_1"],
                    f"<b>{values['bold_1']}</b>",
                    values["example_1"])
                window["example_1"].update(value=example_1_bold)
                window["bold_1"].update(value="")

        elif event == "example_1_lower":
            values["sutta_1"] = values["sutta_1"].lower()
            window["sutta_1"].update(values["sutta_1"])
            values["example_1"] = values["example_1"].lower()
            window["example_1"].update(values["example_1"])

        elif event == "example_1_clean":
            replace_sandhi(
                values["example_1"], "example_1", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["bold_1"], "bold_1", 
                sandhi_dict, hyphenations_dict, window)

        elif event == "example_2_clean":
            replace_sandhi(
                values["example_2"], "example_2", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["bold_2"], "bold_2", 
                sandhi_dict, hyphenations_dict, window)

        elif event == "commentary_clean":
            replace_sandhi(
                values["commentary"], "commentary", 
                sandhi_dict, hyphenations_dict, window)

        elif event == "another_eg_2":
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                default_text = re.sub(r" \d.*$", "", values["lemma_1"])
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=default_text[:-1],
                    title=None,
                    location=(400, 400))
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update(values=[word_to_add])

            source_sutta_example = find_sutta_example(pth, sg, window, values)

            if source_sutta_example is not None:
                try:
                    window["source_2"].update(value=source_sutta_example[0])
                    window["sutta_2"].update(value=source_sutta_example[1])
                    window["example_2"].update(value=source_sutta_example[2])
                except KeyError as e:
                    window["messages"].update(value=str(e), text_color="red")

            flags.example_2 = False

        # bold2
        elif event == "bold_2_button" or event == "bold_2_enter":
            if values["bold_2"]:
                example_2_bold = re.sub(
                    values["bold_2"],
                    f"<b>{values['bold_2']}</b>",
                    values["example_2"])
                window["example_2"].update(value=example_2_bold)
                window["bold_2"].update(value="")

        elif event == "example_2_lower":
            values["sutta_2"] = values["sutta_2"].lower()
            window["sutta_2"].update(values["sutta_2"])
            values["example_2"] = values["example_2"].lower()
            window["example_2"].update(values["example_2"])

        elif event == "synonym":
            if flags.synoyms:
                synoyms = get_synonyms(
                    db_session, values["pos"], values["meaning_1"], values["lemma_1"])
                window["synonym"].update(value=synoyms)
                window["messages"].update(value="synonyms updated")
                flags.synoyms = False

        elif event == "search_for":
            if not values["search_for"]:
                word_no_spaces = re.sub(r" \d.*", "", values["lemma_1"])
                window["search_for"].update(value=word_no_spaces[:-1])

        elif (
            event == "search_for_enter" or
            event == "defintions_search_button"
        ):
            commentary_defintions = None
            try:
                commentary_defintions = find_commentary_defintions(
                    sg, values, db_session)
            except NameError as e:
                window["messages"].update(
                    value=f"turn on the definitions db! {e}", text_color="red")

            if commentary_defintions:
                commentary = ""
                for c in commentary_defintions:
                    commentary += f"({c.ref_code}) {c.commentary}\n"
                commentary = commentary.rstrip("\n")
                window["commentary"].update(value=commentary)

        elif (
            event == "notes_italic_button"
            or event == "notes_italic_bold_enter"
        ):
            if values["notes_italic_bold"]:
                notes_italic = re.sub(
                    values["notes_italic_bold"],
                    f"<i>{values['notes_italic_bold']}</i>",
                    values["notes"])
                window["notes"].update(value=notes_italic)
                window["notes_italic_bold"].update(value="")

        elif event == "notes_bold_button":
            if values["notes_italic_bold"]:
                notes_bold = re.sub(
                    values["notes_italic_bold"],
                    f"<b>{values['notes_italic_bold']}</b>",
                    values["notes"])
                window["notes"].update(value=notes_bold)
                window["notes_italic_bold"].update(value="")


        elif event == "sanskrit":
            if (
                flags.sanskrit 
                and not values["root_key"]
                and not values["sanskrit"]
            ):
                sanskrit = get_sanskrit(db_session, values["construction"])
                window["sanskrit"].update(value=sanskrit)
                flags.sanskrit = False

        elif event == "stem":
            if flags.stem:
                add_stem_pattern(values, window)
                flags.stem = False

        # add word buttons

        elif (
            event == "Clone" 
            or event == "word_to_clone_edit_enter"
            or event == "alt_c" 
        ):
            if values["word_to_clone_edit"]:
                copy_word_from_db(db_session, values, window)
                window["word_to_clone_edit"].update(value="")
            else:
                window["messages"].update(value="No word to copy!", text_color="red")

        elif (
            event == "edit_button"
            or event == "alt_e"
        ):
            if values["word_to_clone_edit"]:
                pali_word_original = edit_word_in_db(db_session, values, window)
                pali_word_original2 = deepcopy(pali_word_original)
                open_in_goldendict(values["word_to_clone_edit"])
                window["word_to_clone_edit"].update(value="")
            else:
                window["messages"].update(value="No word to edit!", text_color="red")

        # gui buttons

        elif (
            event == "clear_button"
            or event == "control_l"
        ):
            clear_errors(window)
            clear_values(values, window, username)
            if username == "primary_user":
                get_next_ids(db_session, window)
            elif username == "deva":
                get_next_ids_dps(db_session, window)
            else:
                # Perform actions for other usernames
                get_next_ids(db_session, window)
            reset_flags(flags)
            window["messages"].update(value="")

        elif (
            event == "test_internal_button"
            or event == "control_t"
            or event == "origin_enter"
        ):
            clear_errors(window)
            flags = individual_internal_tests(
                pth, sg, window, values, flags, username)

            # spell checks
            field = "meaning_1"
            error_field = "meaning_1_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            field = "meaning_lit"
            error_field = "meaning_lit_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            field = "meaning_2"
            error_field = "meaning_2_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            # check allowable characters
            error_dict = test_allowable_characters_gui(values)
            for column, test_value in error_dict.items():
                if column != "origin":
                    if test_value:
                        window[f"{column}_error"].update(value=test_value, text_color="red")
                        window["messages"].update(value="fix bad characters", text_color="red")
                        flags.tested = False
                    else:
                        window[f"{column}_error"].update(value="", text_color="darkgray")

        elif event == "open_tests_button":
            open_internal_tests(pth)
        
        elif event == "open_sanskrit_roots_button":
            subprocess.Popen(
                ["libreoffice", pth.root_families_sanskrit_path])

        elif event == "update_sandhi_button":
            sandhi_dict = make_sandhi_contraction_dict(db_session)


        elif event == "refresh_db_session_button":
            db_session.close()
            db_session = get_db_session(pth.dpd_db_path)

        elif (
            event == "update_db_button1"
            or event == "control_u"
        ):
            if not flags.tested:
                window["messages"].update(value="test first!", text_color="red")
            
            elif not flags.spelling_ok:
                yes_no = sg.popup_yes_no(
                    "There are spelling mistakes. Are you sure you want to continue?",
                    location=(400, 400),
                    modal=True)
                if yes_no == "Yes":
                    flags.spelling_ok = True
                else:
                    continue   
            
            last_button = display_summary(values, window, sg, pali_word_original2)
            
            if last_button == "ok_button":
                
                success, action = udpate_word_in_db(
                    pth, db_session, window, values)
                
                if success:
                    del_syns_if_pos_meaning_changed(db_session, values, pali_word_original2)
                    clear_errors(window)
                    clear_values(values, window, username)
                    if username == "primary_user":
                        get_next_ids(db_session, window)
                    elif username == "deva":
                        get_next_ids_dps(db_session, window)
                    else:
                        # Perform actions for other usernames
                        get_next_ids(db_session, window)
                    reset_flags(flags)
                    remove_word_to_add(values, window, words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))

        elif event == "update_db_button2":
            tests_failed = None
            if not flags.tested:
                tests_failed = sg.popup_ok_cancel(
                    "Tests have failed. Are you sure you want to add to db?",
                    title="Error",
                    location=(400, 400))
            if (
                tests_failed or
                flags.tested
            ):
                last_button = display_summary(values, window, sg, pali_word_original2)
                if last_button == "ok_button":
                    success, action = udpate_word_in_db(
                        pth, db_session, window, values)
                    if success:
                        book_to_add = values["book_to_add"]
                        compare_differences(book_to_add, pth, values, sg, pali_word_original2, action)
                        clear_errors(window)
                        window["dps_id_or_lemma_1"].update(values["lemma_1"])
                        clear_values(values, window, username)
                        if username == "primary_user":
                            get_next_ids(db_session, window)
                        elif username == "deva":
                            get_next_ids_dps(db_session, window)
                        else:
                            # Perform actions for other usernames
                            get_next_ids(db_session, window)
                        reset_flags(flags)
                        remove_word_to_add(values, window, words_to_add_list)
                        window["words_to_add_length"].update(
                            value=len(words_to_add_list))
                        # open_in_goldendict(values["lemma_1"])
                        window["tab_edit_dps"].select()  # type: ignore
                        
        
        elif event == "open_corrections_button":
            edit_corrections(pth)

        elif event == "debug_button":
            print(f"{values}")

        elif (
            event == "stash_button"
            or event == "alt_s"
        ):
            stasher(pth, values, window)

        elif (event == "unstash_button"
            or event == "alt_u"
        ):
            unstasher(pth, window)

        elif event == "split_button":
            lemma_1_old, lemma_1_new = increment_lemma_1(values)
            if username == "deva":
                # add number 1 to lemma_1 for old word if there is no digit
                lemma_1 = values['lemma_1']
                if not re.search(r'\d', lemma_1):
                # Execute code here when lemma_1 doesn't contain any digit
                    if sg.popup_yes_no(f'change lemma_1 of original word to {lemma_1} 1 ?') == 'Yes':
                        id_old = values["id"]
                        add_number_to_pali(pth, db_session, id_old, lemma_1_old)
            window["lemma_1"].update(value=lemma_1_old)
            values["lemma_1"] = lemma_1_old
            stasher(pth, values, window)
            if username == "primary_user":
                get_next_ids(db_session, window)
            elif username == "deva":
                get_next_ids_dps(db_session, window)
            else:
                # Perform actions for other usernames
                get_next_ids(db_session, window)
            window["lemma_1"].update(value=lemma_1_new)
            reset_flags(flags)

            # clear these fields
            clear_fields = [
                "messages", "commentary",
                "synonym", "variant", "notes",  
                "source_1", "sutta_1", "example_1", 
                "source_2", "sutta_2", "example_2",
                "antonym", "synonym", "variant"]
            for c in clear_fields:
                window[c].update(value="")

        elif event == "html_summary_button":
            make_html(pth, [values["lemma_1"]])

        elif (
            event == "save_state_button"
            or event == "control_s"
        ):
            save_gui_state(pth, values, words_to_add_list)
            window["messages"].update(
                    value="saved gui state", text_color="green")

        elif event == "delete_button":
            row_id = values['id']
            lemma_1 = values['lemma_1']
            yes_no = sg.popup_yes_no(
                f"Are you sure you want to delete {row_id} {lemma_1}?",
                location=(400, 400),
                modal=True)
            if yes_no == "Yes":
                success = delete_word(pth, db_session, values, window)
                if success:
                    clear_errors(window)
                    clear_values(values, window, username)
                    if username == "primary_user":
                        get_next_ids(db_session, window)
                    elif username == "deva":
                        get_next_ids_dps(db_session, window)
                    else:
                        # Perform actions for other usernames
                        get_next_ids(db_session, window)
                    reset_flags(flags)
                    window["messages"].update(
                        value=f"{row_id} '{lemma_1}' deleted", text_color="white")

        elif event == "save_and_close_button":
            window["messages"].update(
                value="backing up db to csvs", text_color="white")
            if username == "primary_user":
                backup_dpd_headwords_and_roots(pth)

                save_gui_state(pth, values, words_to_add_list)
                window["messages"].update(
                        value="saved gui state", text_color="green")
            elif username == "deva":
                backup_ru_sbs()
            break

        # fix sandhi events

        # sandhi rules
        elif event == "add_sandhi_rule":
            add_sandhi_rule(pth, window, values)

        elif event == "open_sandhi_rules":
            open_sandhi_rules(pth)

        # sandhi corrections
        elif event == "add_sandhi_correction":
            add_sandhi_correction(pth, window, values)

        elif event == "open_sandhi_corrections":
            open_sandhi_corrections(pth)

        # spelling mistakes
        elif event == "add_spelling_mistake":
            add_spelling_mistake(pth, window, values)

        elif event == "open_spelling_mistakes":
            open_spelling_mistakes(pth)

        # variant readings
        elif event == "add_variant_reading":
            add_variant_reading(pth, window, values)

        elif event == "open_variant_readings":
            open_variant_readings(pth)

        elif event == "open_sandhi_ok":
            open_sandhi_ok(pth)

        elif event == "open_sandhi_exceptions":
            open_sandhi_exceptions(pth)

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
            for value in hide_list_all:
                window[value].update(visible=username == "deva")

        elif event == "show_fields_root":

            has_value_list = make_has_values_list(values)

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
                if value not in has_value_list:
                    window[value].update(visible=False)
            for value in hide_list_all:
                window[value].update(visible=username == "deva")
            window["get_family_root"].update(visible=True)
            window["get_root_base"].update(visible=True)
            window["get_root_sign"].update(visible=True)
            flags.show_fields = False

        elif event == "show_fields_compound":

            has_value_list = make_has_values_list(values)

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
                if value not in has_value_list:
                    window[value].update(visible=False)
            for value in hide_list_all:
                window[value].update(visible=username == "deva")
            flags.show_fields = False

        elif event == "show_fields_word":

            has_value_list = make_has_values_list(values)

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
                if value not in has_value_list:
                    window[value].update(visible=False)
            for value in hide_list_all:
                window[value].update(visible=username == "deva")
            flags.show_fields = False

        # test db tab buttons

        elif event == "test_db_internal":
            db_internal_tests(db_session, pth, sg, window, flags)

        elif event == "test_next":
            flags.test_next = True

        elif event == "test_edit":
            open_internal_tests(pth)

        # combo events

        elif event.endswith("-key"):
            combo = window[event.replace("-key", "")]
            combo.filter()  # type: ignore

        elif event.endswith("-enter"):
            combo = window[event.replace("-enter", "")]
            combo.complete()  # type: ignore

        elif event.endswith("-focus_out"):
            combo = window[event.replace("-focus_out", "")]
            combo.hide_tooltip()  # type: ignore

        # DPS tab

        # dps hide fields logic
        elif event == "dps_show_fields_all":
            for value in values:
                window[value].update(visible=True)
                window["dps_sbs_meaning"].update(visible=True)
                window["dps_sbs_meaning_error"].update(visible=True)
                window["dps_sbs_notes"].update(visible=True)
                window["dps_sbs_notes_error"].update(visible=True)
                window["dps_sbs_chant_pali_1"].update(visible=True)
                window["dps_sbs_chant_pali_1_error"].update(visible=True)
                window["dps_sbs_chant_eng_1"].update(visible=True)
                window["dps_sbs_chapter_1"].update(visible=True)
                window["dps_sbs_chant_pali_2"].update(visible=True)
                window["dps_sbs_chant_pali_2_error"].update(visible=True)
                window["dps_sbs_chant_eng_2"].update(visible=True)
                window["dps_sbs_chapter_2"].update(visible=True)
                window["dps_sbs_chant_pali_3"].update(visible=True)
                window["dps_sbs_chant_pali_3_error"].update(visible=True)
                window["dps_sbs_chant_eng_3"].update(visible=True)
                window["dps_sbs_chapter_3"].update(visible=True)
                window["dps_sbs_chant_pali_4"].update(visible=True)
                window["dps_sbs_chant_pali_4_error"].update(visible=True)
                window["dps_sbs_chant_eng_4"].update(visible=True)
                window["dps_sbs_chapter_4"].update(visible=True)

                dps_flags.show_fields = True

        elif event == "dps_show_fields_no_sbs":
            hide_list = [
                "dps_sbs_meaning", "dps_sbs_meaning_error", "dps_sbs_notes", "dps_sbs_notes_error", 
                "dps_sbs_chant_pali_1", "dps_sbs_chant_eng_1", "dps_sbs_chapter_1",
                "dps_sbs_chant_pali_1_error",
                "dps_sbs_chant_pali_2", "dps_sbs_chant_eng_2", "dps_sbs_chapter_2",
                "dps_sbs_chant_pali_2_error",
                "dps_sbs_chant_pali_3", "dps_sbs_chant_eng_3", "dps_sbs_chapter_3",
                "dps_sbs_chant_pali_3_error",
                "dps_sbs_chant_pali_4", "dps_sbs_chant_eng_4", "dps_sbs_chapter_4",
                "dps_sbs_chant_pali_4_error",
            ]
            for value in values:
                window[value].update(visible=True)
            for value in hide_list:
                window[value].update(visible=False)
            dps_flags.show_fields = False

        # tabs jumps to next field in multiline
        if event == "dps_meaning_tab":
            focus = window['dps_meaning'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_ru_online_suggestion_tab":
            focus = window['dps_ru_online_suggestion'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_ru_meaning_tab":
            focus = window['dps_ru_meaning'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_meaning_tab":
            focus = window['dps_sbs_meaning'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_notes_tab":
            focus = window['dps_notes'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_notes_online_suggestion_tab":
            focus = window['dps_ru_online_suggestion'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_ru_notes_tab":
            focus = window['dps_ru_notes'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_notes_tab":
            focus = window['dps_sbs_notes'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_example_1_tab":
            focus = window['dps_example_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_example_2_tab":
            focus = window['dps_example_2'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_example_1_tab":
            focus = window['dps_sbs_example_1'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_example_2_tab":
            focus = window['dps_sbs_example_2'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_example_3_tab":
            focus = window['dps_sbs_example_3'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "dps_sbs_example_4_tab":
            focus = window['dps_sbs_example_4'].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "online_suggestion_tab":
            focus = window['online_suggestion'].get_next_focus()
            if focus is not None:
                focus.set_focus()

        # fetch word from db
        if (
            event == "dps_id_or_lemma_1_enter" or
            event == "dps_id_or_lemma_1_button"
        ):
            if values["dps_id_or_lemma_1"]:
                dpd_word = fetch_id_or_lemma_1(db_session, values, "dps_id_or_lemma_1")
                if dpd_word:
                    ru_word = fetch_ru(db_session, dpd_word.id)
                    sbs_word = fetch_sbs(db_session, dpd_word.id)
                    open_in_goldendict(dpd_word.lemma_1)
                    populate_dps_tab(
                        dpspth, values, window, dpd_word, ru_word, sbs_word)
                    window["messages"].update(
                        value=f'editing {values["dps_id_or_lemma_1"]}', text_color="PaleTurquoise")
                else:
                    window["messages"].update(
                        value="not a valid id or lemma_1", text_color="red")

        elif event == "dps_synonym":
            if dps_flags.synoyms:
                error_field = "dps_synonym_error"
                synoyms = dps_get_synonyms(db_session, values["dps_pos"], values["dps_meaning"], window, error_field)
                window["dps_synonym"].update(value=synoyms)
                dps_flags.synoyms = False

        # buttons for sbs_ex_1
        # search sbs_ex1
        elif (
            (
                event == "dps_sbs_example_1"
                and dps_flags.sbs_example_1 and
                not values["dps_sbs_example_1"] and
                values["lemma_1"] and
                values["word_to_add"]
            ) or
            (
                event == "dps_sbs_source_1" and
                dps_flags.sbs_example_1 and
                not values["dps_sbs_example_1"] and
                values["dps_lemma_1"] and
                values["word_to_add"]
            ) or
            (
                event == "dps_sbs_sutta_1" and
                dps_flags.sbs_example_1 and
                not values["dps_sbs_example_1"] and
                values["dps_lemma_1"] and
                values["word_to_add"]
            ) or
            event == "dps_another_eg_1"
        ):

            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add
            else:
                book_to_add = sg.popup_get_text(
                    "Which book?", default_text=values["book_to_add"], 
                    title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["dps_lemma_1"][:-1],
                    title=None,
                    location=(400, 400))
                if word_to_add:
                    values["word_to_add"] = [word_to_add]
                    window["word_to_add"].update(values=[word_to_add])

            if (
                test_book_to_add(values, window) and
                values["book_to_add"] and
                values["word_to_add"]
            ):
                source_sutta_example = find_sutta_example(pth, sg, window, values)

                if source_sutta_example is not None:
                    try:
                        window["dps_sbs_source_1"].update(value=source_sutta_example[0])
                        window["dps_sbs_sutta_1"].update(value=source_sutta_example[1])
                        window["dps_sbs_example_1"].update(value=source_sutta_example[2])
                    except KeyError as e:
                        window["messages"].update(value=str(e), text_color="red")

                dps_flags.sbs_example_1 = False

        # dps bold1
        elif event == "dps_bold_1_button" or event == "dps_bold_1_enter":
            if values["dps_bold_1"]:
                dps_example_1_bold = re.sub(
                    values["dps_bold_1"],
                    f"<b>{values['dps_bold_1']}</b>",
                    values["dps_sbs_example_1"])
                window["dps_sbs_example_1"].update(value=dps_example_1_bold)
                window["dps_bold_1"].update(value="")

        # dps lower1
        elif event == "dps_example_1_lower":
            values["dps_sbs_sutta_1"] = values["dps_sbs_sutta_1"].lower()
            window["dps_sbs_sutta_1"].update(values["dps_sbs_sutta_1"])
            values["dps_sbs_example_1"] = values["dps_sbs_example_1"].lower()
            window["dps_sbs_example_1"].update(values["dps_sbs_example_1"])

        # dps clean1
        elif event == "dps_example_1_clean":
            replace_sandhi(
                values["dps_sbs_example_1"], "dps_sbs_example_1", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["dps_bold_1"], "dps_bold_1", 
                sandhi_dict, hyphenations_dict, window)

        # buttons for sbs_ex_2

        # dps clean2
        elif event == "dps_example_2_clean":
            replace_sandhi(
                values["dps_sbs_example_2"], "dps_sbs_example_2", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["dps_bold_2"], "dps_bold_2", 
                sandhi_dict, hyphenations_dict, window)

        # search sbs_ex2
        elif event == "dps_another_eg_2":
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                values["book_to_add"] = book_to_add

            else:
                book_to_add = sg.popup_get_text(
                    "Which book?", default_text=values["book_to_add"], 
                    title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["dps_lemma_1"],
                    title=None,
                    location=(400, 400))
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update(values=[word_to_add])

            source_sutta_example = find_sutta_example(pth, sg, window, values)

            if source_sutta_example is not None:
                try:
                    window["dps_sbs_source_2"].update(value=source_sutta_example[0])
                    window["dps_sbs_sutta_2"].update(value=source_sutta_example[1])
                    window["dps_sbs_example_2"].update(value=source_sutta_example[2])
                except KeyError as e:
                    window["messages"].update(value=str(e), text_color="red")

            dps_flags.sbs_example_2 = False

        # dps bold2
        elif event == "dps_bold_2_button" or event == "dps_bold_2_enter":
            if values["dps_bold_2"]:
                example_2_bold = re.sub(
                    values["dps_bold_2"],
                    f"<b>{values['dps_bold_2']}</b>",
                    values["dps_sbs_example_2"])
                window["dps_sbs_example_2"].update(value=example_2_bold)
                window["dps_bold_2"].update(value="")

        # dps lower2
        elif event == "dps_example_2_lower":
            values["dps_sbs_sutta_2"] = values["dps_sbs_sutta_2"].lower()
            window["dps_sbs_sutta_2"].update(values["dps_sbs_sutta_2"])
            values["dps_sbs_example_2"] = values["dps_sbs_example_2"].lower()
            window["dps_sbs_example_2"].update(values["dps_sbs_example_2"])

        # buttons for sbs_ex_3

        # dps clean3
        elif event == "dps_example_3_clean":
            replace_sandhi(
                values["dps_sbs_example_3"], "dps_sbs_example_3", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["dps_bold_3"], "dps_bold_3", 
                sandhi_dict, hyphenations_dict, window)

        # search sbs_ex3
        elif event == "dps_another_eg_3":
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                values["book_to_add"] = book_to_add

            else:
                book_to_add = sg.popup_get_text(
                    "Which book?", default_text=values["book_to_add"], 
                    title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["dps_lemma_1"],
                    title=None,
                    location=(400, 400))
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update(values=[word_to_add])

            source_sutta_example = find_sutta_example(pth, sg, window, values)

            if source_sutta_example is not None:
                try:
                    window["dps_sbs_source_3"].update(value=source_sutta_example[0])
                    window["dps_sbs_sutta_3"].update(value=source_sutta_example[1])
                    window["dps_sbs_example_3"].update(value=source_sutta_example[2])
                except KeyError as e:
                    window["messages"].update(value=str(e), text_color="red")

            dps_flags.sbs_example_3 = False

        # dps bold3
        elif event == "dps_bold_3_button" or event == "dps_bold_3_enter":
            if values["dps_bold_3"]:
                example_3_bold = re.sub(
                    values["dps_bold_3"],
                    f"<b>{values['dps_bold_3']}</b>",
                    values["dps_sbs_example_3"])
                window["dps_sbs_example_3"].update(value=example_3_bold)
                window["dps_bold_3"].update(value="")

        # dps lower3
        elif event == "dps_example_3_lower":
            values["dps_sbs_sutta_3"] = values["dps_sbs_sutta_3"].lower()
            window["dps_sbs_sutta_3"].update(values["dps_sbs_sutta_3"])
            values["dps_sbs_example_3"] = values["dps_sbs_example_3"].lower()
            window["dps_sbs_example_3"].update(values["dps_sbs_example_3"])
            
        # buttons for sbs_ex_4

        # clean4
        elif event == "dps_example_4_clean":
            replace_sandhi(
                values["dps_sbs_example_4"], "dps_sbs_example_4", 
                sandhi_dict, hyphenations_dict, window)
            replace_sandhi(
                values["dps_bold_4"], "dps_bold_4", 
                sandhi_dict, hyphenations_dict, window)

        # search sbs_ex4
        elif event == "dps_another_eg_4":
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None,
                    location=(400, 400))
                values["book_to_add"] = book_to_add

            else:
                book_to_add = sg.popup_get_text(
                    "Which book?", default_text=values["book_to_add"], 
                    title=None,
                    location=(400, 400))
                if book_to_add:
                    values["book_to_add"] = book_to_add

            if values["word_to_add"] == []:
                word_to_add = sg.popup_get_text(
                    "What word?", default_text=values["dps_lemma_1"],
                    title=None,
                    location=(400, 400))
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update(values=[word_to_add])

            source_sutta_example = find_sutta_example(pth, sg, window, values)

            if source_sutta_example is not None:
                try:
                    window["dps_sbs_source_4"].update(value=source_sutta_example[0])
                    window["dps_sbs_sutta_4"].update(value=source_sutta_example[1])
                    window["dps_sbs_example_4"].update(value=source_sutta_example[2])
                except KeyError as e:
                    window["messages"].update(value=str(e), text_color="red")

            dps_flags.sbs_example_4 = False

        # dps bold4
        elif event == "dps_bold_4_button" or event == "dps_bold_4_enter":
            if values["dps_bold_4"]:
                example_4_bold = re.sub(
                    values["dps_bold_4"],
                    f"<b>{values['dps_bold_4']}</b>",
                    values["dps_sbs_example_4"])
                window["dps_sbs_example_4"].update(value=example_4_bold)
                window["dps_bold_4"].update(value="")

        # dps lower4
        elif event == "dps_example_4_lower":
            values["dps_sbs_sutta_4"] = values["dps_sbs_sutta_4"].lower()
            window["dps_sbs_sutta_4"].update(values["dps_sbs_sutta_4"])
            values["dps_sbs_example_4"] = values["dps_sbs_example_4"].lower()
            window["dps_sbs_example_4"].update(values["dps_sbs_example_4"])

        # google translate buttons
        elif event == "dps_google_translate_button":
            field = "dps_ru_online_suggestion"
            error_field = "dps_ru_meaning_suggestion_error"
            translate_to_russian_googletrans(values["dps_meaning"], field, error_field, window)

        elif event == "dps_notes_google_translate_button":
            field = "dps_notes_online_suggestion"
            error_field = "dps_ru_notes_suggestion_error"
            translate_to_russian_googletrans(values["dps_notes"], field, error_field, window)

        # openai translate buttons
        elif event == "dps_openai_translate_button_1":
            field = "dps_ru_online_suggestion"
            error_field = "dps_ru_meaning_suggestion_error"
            ru_translate_with_openai(values['sbs_example_for_suggestion'], values['dps_example_1'], values['dps_sbs_example_1'], values['dps_sbs_example_2'], values['dps_sbs_example_3'], values['dps_sbs_example_4'], dpspth, pth, values['dps_meaning'], values['dps_lemma_1'], values['dps_grammar'], field, error_field, window, "3")

        elif event == "dps_openai_translate_button_2":
            field = "dps_ru_online_suggestion"
            error_field = "dps_ru_meaning_suggestion_error"
            ru_translate_with_openai(values['sbs_example_for_suggestion'], values['dps_example_1'], values['dps_sbs_example_1'], values['dps_sbs_example_2'], values['dps_sbs_example_3'], values['dps_sbs_example_4'], dpspth, pth, values['dps_meaning'], values['dps_lemma_1'], values['dps_grammar'], field, error_field, window, "4")

        elif event == "dps_notes_openai_translate_button":
            field = "dps_notes_online_suggestion"
            error_field = "dps_ru_notes_suggestion_error"
            ru_notes_translate_with_openai(dpspth, pth, values['dps_notes'], values['dps_lemma_1'], values['dps_grammar'], field, error_field, window)

        # in dpd tab
        elif event == "online_suggestion_button_1":
            field = "online_suggestion"
            error_field = "online_suggestion_error"
            en_translate_with_openai(dpspth, pth, values['lemma_1'], values['grammar'], values['example_1'], field, error_field, window, "3")

        elif event == "online_suggestion_button_2":
            field = "online_suggestion"
            error_field = "online_suggestion_error"
            en_translate_with_openai(dpspth, pth, values['lemma_1'], values['grammar'], values['example_1'], field, error_field, window, "4")

        # copy ru sugestions buttons
        elif event == "dps_copy_meaning_button":
            error_field = "dps_ru_meaning_suggestion_error"
            copy_and_split_content('dps_ru_online_suggestion', 'dps_ru_meaning', 'dps_ru_meaning_lit', error_field, window, values)

        elif event == "dps_notes_copy_meaning_button":
            error_field = "dps_ru_notes_suggestion_error"
            copy_and_split_content('dps_notes_online_suggestion', 'dps_ru_notes', '', error_field, window, values)

        # movement in this field triggers spellcheck dps tab
        elif event == "ru_add_spelling":
            field = "dps_ru_meaning"
            error_field = "dps_ru_meaning_error"
            ru_check_spelling(dpspth, field, error_field, values, window)

        elif event == "dps_ru_check_spelling_button":
            field = "dps_ru_meaning"
            error_field = "dps_ru_meaning_error"
            ru_check_spelling(dpspth, field, error_field, values, window)

            field = "dps_ru_meaning_lit"
            error_field = "dps_ru_meaning_lit_error"
            ru_check_spelling(dpspth, field, error_field, values, window)
            
            field = "dps_ru_notes"
            error_field = "dps_ru_notes_error"
            ru_check_spelling(dpspth, field, error_field, values, window)

            field = "dps_sbs_meaning"
            error_field = "dps_sbs_meaning_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            field = "dps_sbs_notes"
            error_field = "dps_sbs_notes_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)

            # dps repetition check
            field = "dps_ru_meaning"
            error_field = "dps_repetition_meaning_error"
            check_repetition(field, error_field, values, window)

        elif event == "dps_ru_add_spelling_button":
            word = values["dps_ru_add_spelling"]
            ru_add_spelling(dpspth, word)
            window["messages"].update(
                value=f"{word} added to ru dictionary", text_color="white")

        elif event == "dps_ru_edit_spelling_button":
            ru_edit_spelling(dpspth)

        # choice from dropdown sbs chats

        if event == "dps_sbs_chant_pali_1":
            chant = values["dps_sbs_chant_pali_1"]
            error_field = "dps_sbs_chant_pali_1_error"
            update_sbs_chant(dpspth, 1, chant, error_field, window)

        elif event == "dps_sbs_chant_pali_2":
            error_field = "dps_sbs_chant_pali_2_error"
            update_sbs_chant(
                dpspth, 2, values["dps_sbs_chant_pali_2"], error_field, window)

        elif event == "dps_sbs_chant_pali_3":
            error_field = "dps_sbs_chant_pali_3_error"
            update_sbs_chant(
                dpspth, 3, values["dps_sbs_chant_pali_3"], error_field, window)

        elif event == "dps_sbs_chant_pali_4":
            error_field = "dps_sbs_chant_pali_4_error"
            update_sbs_chant(
                dpspth, 4, values["dps_sbs_chant_pali_4"], error_field, window)

        # dps_examples buttons

        elif event == "dps_copy_ex_1_to_1_button":
            copy_dpd_examples(1, 1, window, values)

        elif event == "dps_copy_ex_1_to_2_button":
            copy_dpd_examples(1, 2, window, values)

        elif event == "dps_copy_ex_1_to_3_button":
            copy_dpd_examples(1, 3, window, values)

        elif event == "dps_copy_ex_1_to_4_button":
            copy_dpd_examples(1, 4, window, values)

        elif event == "dps_copy_ex_2_to_1_button":
            copy_dpd_examples(2, 1, window, values)

        elif event == "dps_copy_ex_2_to_2_button":
            copy_dpd_examples(2, 2, window, values)

        elif event == "dps_copy_ex_2_to_3_button":
            copy_dpd_examples(2, 3, window, values)

        elif event == "dps_copy_ex_2_to_4_button":
            copy_dpd_examples(2, 4, window, values)

        # sbs_examples buttons

        elif event in ("dps_swap_ex_1_with_2_button", "dps_swap_ex_2_with_1_button"):
            swap_sbs_examples(1, 2, window, values)

        elif event in ("dps_swap_ex_1_with_3_button", "dps_swap_ex_3_with_1_button"):
            swap_sbs_examples(1, 3, window, values)

        elif event in ("dps_swap_ex_1_with_4_button", "dps_swap_ex_4_with_1_button"):
            swap_sbs_examples(1, 4, window, values)

        elif event in ("dps_swap_ex_2_with_3_button", "dps_swap_ex_3_with_2_button"):
            swap_sbs_examples(2, 3, window, values)

        elif event in ("dps_swap_ex_2_with_4_button", "dps_swap_ex_4_with_2_button"):
            swap_sbs_examples(2, 4, window, values)

        elif event in ("dps_swap_ex_3_with_4_button", "dps_swap_ex_4_with_3_button"):
            swap_sbs_examples(3, 4, window, values)

        elif event == "dps_remove_example_1_button":
            remove_sbs_example(1, window)
            window["messages"].update(
                    value="sbs_ex_1 removed", text_color="white")

        elif event == "dps_remove_example_2_button":
            remove_sbs_example(2, window)
            window["messages"].update(
                    value="sbs_ex_2 removed", text_color="white")

        elif event == "dps_remove_example_3_button":
            remove_sbs_example(3, window)
            window["messages"].update(
                    value="sbs_ex_3 removed", text_color="white")

        elif event == "dps_remove_example_4_button":
            remove_sbs_example(4, window)
            window["messages"].update(
                    value="sbs_ex_4 removed", text_color="white")

        elif event == "dps_stash_ex_1_button":
            error_field = "dps_buttons_ex_1_error"
            stash_values_from(dpspth, values, 1, window, error_field)
            window["messages"].update(
                value="sbs_ex_1 stashed", text_color="white")

        elif event == "dps_stash_ex_2_button":
            error_field = "dps_buttons_ex_2_error"
            stash_values_from(dpspth, values, 2, window, error_field)
            window["messages"].update(
                value="sbs_ex_2 stashed", text_color="white")

        elif event == "dps_stash_ex_3_button":
            error_field = "dps_buttons_ex_3_error"
            stash_values_from(dpspth, values, 3, window, error_field)
            window["messages"].update(
                value="sbs_ex_3 stashed", text_color="white")

        elif event == "dps_stash_ex_4_button":
            error_field = "dps_buttons_ex_4_error"
            stash_values_from(dpspth, values, 4, window, error_field)
            window["messages"].update(
                value="sbs_ex_4 stashed", text_color="white")

        elif event == "dps_unstash_ex_1_button":
            error_field = "dps_buttons_ex_1_error"
            unstash_values_to(dpspth, window, 1, error_field)
            window["messages"].update(
                value="unstashed to sbs_ex_1", text_color="white")

        elif event == "dps_unstash_ex_2_button":
            error_field = "dps_buttons_ex_2_error"
            unstash_values_to(dpspth, window, 2, error_field)
            window["messages"].update(
                value="unstashed to sbs_ex_2", text_color="white")

        elif event == "dps_unstash_ex_3_button":
            error_field = "dps_buttons_ex_3_error"
            unstash_values_to(dpspth, window, 3, error_field)
            window["messages"].update(
                value="unstashed to sbs_ex_3", text_color="white")

        elif event == "dps_unstash_ex_4_button":
            error_field = "dps_buttons_ex_4_error"
            unstash_values_to(dpspth, window, 4, error_field)
            window["messages"].update(
                value="unstashed to sbs_ex_4", text_color="white")

        # dps db buttons:

        elif event == "dps_test_internal_button":
            dpd_word = fetch_id_or_lemma_1(db_session, values, "dps_id_or_lemma_1")
            if dpd_word:

                clear_errors(window)

                dps_flags = dps_individual_internal_tests(
                    dpspth, sg, window, values, dps_flags)
                
                # dps spell checks
                field = "dps_ru_meaning"
                error_field = "dps_ru_meaning_error"
                ru_check_spelling(dpspth, field, error_field, values, window)

                field = "dps_ru_meaning_lit"
                error_field = "dps_ru_meaning_lit_error"
                ru_check_spelling(dpspth, field, error_field, values, window)

                field = "dps_ru_notes"
                error_field = "dps_ru_notes_error"
                ru_check_spelling(dpspth, field, error_field, values, window)

                field = "dps_sbs_meaning"
                error_field = "dps_sbs_meaning_error"
                flags = check_spelling(pth, field, error_field, values, window, flags)

                field = "dps_sbs_notes"
                error_field = "dps_sbs_notes_error"
                flags = check_spelling(pth, field, error_field, values, window, flags)

                # dps repetition check
                field = "dps_ru_meaning"
                error_field = "dps_repetition_meaning_error"
                check_repetition(field, error_field, values, window)

                # dps check allowable characters
                error_dict = test_allowable_characters_gui_dps(values)
                for column, test_value in error_dict.items():
                    if column != "origin":
                        if test_value:
                            window[f"dps_{column}_error"].update(value=test_value, text_color="red")
                            window["messages"].update(value="fix bad characters", text_color="red")
                            flags.tested = False
                        else:
                            window[f"dps_{column}_error"].update(value="", text_color="darkgray")

            else:
                window["messages"].update(
                    value="not a valid id or lemma_1", text_color="red")

        elif event == "dps_update_db_button":
            if not dps_flags.tested:
                window["messages"].update(value="test first!", text_color="red")
            else:
                dpd_word = fetch_id_or_lemma_1(db_session, values, "dps_id_or_lemma_1")
                if dpd_word:
                    ru_word = fetch_ru(db_session, dpd_word.id)
                    sbs_word = fetch_sbs(db_session, dpd_word.id)
                    original_values = dps_get_original_values(values, dpd_word, ru_word, sbs_word)
                    last_button = display_dps_summary(values, window, sg, original_values)
                    if last_button == "dps_ok_button":
                        open_in_goldendict(values["dps_id_or_lemma_1"])
                        dps_update_db(pth, db_session, values, window, dpd_word, ru_word, sbs_word)
                        clear_dps(values, window)
                        clear_errors(window)
                        dps_reset_flags(dps_flags)
                else:
                    window["messages"].update(
                        value="not a valid id or lemma_1", text_color="red")

        # dps gui buttons:

        elif event == "dps_clear_button":
            clear_dps(values, window)
            dps_reset_flags(dps_flags)
            clear_errors(window)
            window["messages"].update(
                        value="cleared", text_color="SteelBlue")

        elif event == "dps_reset_button":
            dpd_word = fetch_id_or_lemma_1(db_session, values, "dps_id_or_lemma_1")
            if dpd_word:
                ru_word = fetch_ru(db_session, dpd_word.id)
                sbs_word = fetch_sbs(db_session, dpd_word.id)
                clear_dps(values, window)
                populate_dps_tab(
                    dpspth, values, window, dpd_word, ru_word, sbs_word)
                window["messages"].update(
                        value="reset", text_color="Wheat")
            else:
                window["messages"].update(
                        value="not a valid id or lemma_1", text_color="red")

        elif event == "dps_stash_button":
            with open(pth.stash_path, "wb") as f:
                pickle.dump(values, f)
            window["messages"].update(
                value=f"{values['dps_lemma_1']} stashed", text_color="white")

        elif event == "dps_unstash_button":
            with open(pth.stash_path, "rb") as f:
                unstash = pickle.load(f)
                for key, value in unstash.items():
                    window[key].update(value)
            window["messages"].update(
                value=f"{values['dps_lemma_1']} unstashed", text_color="white")

        elif event == "dps_open_tests_button":
            dps_open_internal_tests(dpspth)

        elif event == "dps_open_log_in_terminal_button":
            tail_log()

        elif event == "dps_summary_button":
            dpd_word = fetch_id_or_lemma_1(db_session, values, "dps_id_or_lemma_1")
            if dpd_word:
                ru_word = fetch_ru(db_session, dpd_word.id)
                sbs_word = fetch_sbs(db_session, dpd_word.id)
                original_values = dps_get_original_values(values, dpd_word, ru_word, sbs_word)
                display_dps_summary(values, window, sg, original_values)
            else:
                window["messages"].update(
                    value="not a valid id or lemma_1", text_color="red")

        elif event == "dps_html_summary_button":
            make_html(pth, [values["dps_lemma_1"]])


        # dps in word to add tab

        # add book
        elif event == "dps_books_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = dps_make_words_to_add_list(
                    db_session, pth, window, values["book_to_add"])

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        value=f"added missing words from {values['book_to_add']}",
                        text_color="white")
                else:
                    window["messages"].update(
                        value="empty list, try again", text_color="red")

        # add sutta (dpd)
        elif event == "sutta_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = dps_make_words_to_add_list_sutta(
                    db_session, pth, values["sutta_to_add"], values["book_to_add"])

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        value=f"added missing words from {values['sutta_to_add']}",
                        text_color="white")
                else:
                    window["messages"].update(
                        value="empty list, try again", text_color="red")


        # add sutta (dps)
        elif event == "dps_sutta_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = dps_make_words_to_add_list_sutta(
                    db_session, pth, values["sutta_to_add"], values["book_to_add"])

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(
                        value=len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        value=f"added missing words from {values['sutta_to_add']}",
                        text_color="white")
                else:
                    window["messages"].update(
                        value="empty list, try again", text_color="red")

        # from source
        elif event == "dps_add_from_source":
            words_to_add_list = words_in_db_from_source(db_session, values["source_to_add"])

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value=f"added missing words from {values['source_to_add']}",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")


        # add words from text.txt (dps)
        elif event == "dps_from_txt_to_add_button":
            words_to_add_list = dps_make_words_to_add_list_from_text(dpspth, db_session, pth)

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value="added missing words from text.txt",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        # add words from text.txt which do not have source
        elif event == "dps_from_txt_to_add_considering_source_button":
            words_to_add_list = dps_make_words_to_add_list_from_text_filtered(dpspth, db_session, pth, values["source_to_add"])
            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value="added missing words from text.txt",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        # add words from text.txt which do not have field
        elif event == "dps_from_txt_to_add_considering_field_button":
            words_to_add_list = dps_make_words_to_add_list_from_text_no_field(dpspth, db_session, pth, values["field_for_id_list"])
            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value="added missing words from text.txt",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")


        # add words from id list
        elif event == "dps_word_from_id_list_button":
            words_to_add_list = fetch_matching_words_from_db_with_conditions(dpspth, db_session, values["field_for_id_list"])

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value=f"added missing words from {values['source_to_add']}",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        
        # add words from tests
        elif event == "from_test_to_add_button":
            words_to_add_list = read_tsv_words(dpspth.dps_test_1_path)

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value="added words from tests",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        # add words from temp id list
        elif event == "from_temp_id_list_to_add_button":
            file_path = dpspth.id_temp_list_path

            words_to_add_list = fetch_matching_words_from_db(file_path, db_session)

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value=f"added words from {file_path}",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        # add words which has source in field
        elif event == "dps_source_in_field":
            words_to_add_list = words_in_db_with_value_in_field_sbs(db_session, values["field_for_id_list"], values["source_to_add"])

            if words_to_add_list != []:
                values["word_to_add"] = [words_to_add_list[0]]
                window["word_to_add"].update(values=words_to_add_list)
                window["words_to_add_length"].update(
                    value=len(words_to_add_list))
                print(values)
                open_in_goldendict(words_to_add_list[0])
                window["messages"].update(
                    value=f"added words which has {values['source_to_add']} in {values['field_for_id_list']}",
                    text_color="white")
            else:
                window["messages"].update(
                    value="empty list, try again", text_color="red")

        # sent request to simsapa               
        elif event == "send_sutta_study_request_button":
            print(values)
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                send_sutta_study_request(values["word_to_add"][0], values['sutta_to_add'], values['source_to_add'])

        # edit word in DPS
        elif event == "dps_edit_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                window["tab_edit_dps"].select()  # type: ignore
                window["dps_id_or_lemma_1"].update(values["word_to_add"][0])

        # edit word in DPD
        elif event == "dpd_edit_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                window["tab_edit_dpd"].select()  # type: ignore
                window["word_to_clone_edit"].update(values["word_to_add"][0])

        # update sbs value
        elif event == "dps_update_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                daily_record_update(window, pth, "check", values["word_to_add"][0])
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                update_field(db_session, values["field_for_id_list"], values["word_to_add"][0], values["source_to_add"])
                window["messages"].update(
                        value="category updated",
                        text_color="white")
                        
        # mark sbs value
        elif event == "dps_mark_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                daily_record_update(window, pth, "check", values["word_to_add"][0])
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
                update_field_with_change(db_session, values["field_for_id_list"], values["word_to_add"][0], values["source_to_add"])
                window["messages"].update(
                        value="word marked",
                        text_color="white")


        elif event == "dps_save_gui_state_1":
            save_gui_state(pth, values, words_to_add_list)
            window["messages"].update(
                    value="saved gui state (1)", text_color="green")

        elif event == "dps_save_gui_state_2":
            save_gui_state_dps(dpspth, values, words_to_add_list)
            window["messages"].update(
                    value="saved gui state (2)", text_color="lime")


        elif event == "dps_load_gui_state_1":
            try:
                saved_values, words_to_add_list = load_gui_state(pth)
                for key, value in saved_values.items():
                    window[key].update(value)
                window["word_to_add"].update(words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
            except FileNotFoundError:
                window["messages"].update(value="previously saved state not found. select a book to add",
                    text_color="white")
                words_to_add_list = []

        elif event == "dps_load_gui_state_2":
            try:
                saved_values, words_to_add_list = load_gui_state_dps(dpspth)
                for key, value in saved_values.items():
                    window[key].update(value)
                window["word_to_add"].update(words_to_add_list)
                window["words_to_add_length"].update(value=len(words_to_add_list))
            except FileNotFoundError:
                window["messages"].update(value="previously saved state (2) not found. select a book to add",
                    text_color="white")
                words_to_add_list = []


        # test db tab                

        elif event == "ru_test_db_internal":
            dps_dpd_db_internal_tests(dpspth, db_session, pth, sg, window, flags)

        # dps test tab

        elif event == "dps_test_db_internal":
            dps_db_internal_tests(dpspth, pth, db_session, sg, window, dps_flags)

        elif event == "dps_test_next":
            dps_flags.test_next = True

        elif event == "dps_test_edit":
            dps_open_internal_tests(dpspth)

    window.close()


if __name__ == "__main__":
    main()
