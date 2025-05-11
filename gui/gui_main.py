#!/usr/bin/env python3

"""Main program to run the GUI."""

import json
import re
import subprocess
from copy import deepcopy

import pyperclip
import PySimpleGUI as sg  # type: ignore
from rich import print

from db.db_helpers import get_db_session
from db_tests.single.test_allowable_characters import (
    test_allowable_characters_gui,
)
from gui.functions import (
    Flags,
    add_sandhi_correction,
    add_sandhi_rule,
    add_spelling,
    add_spelling_mistake,
    add_stem_pattern,
    add_to_word_to_add,
    add_variant_reading,
    check_spelling,
    clear_errors,
    clear_values,
    compare_differences,
    display_summary,
    edit_spelling,
    example_load,
    example_save,
    find_sutta_example,
    increment_lemma_1,
    load_gui_state,
    make_compound_construction,
    make_construction,
    make_lemma_clean,
    make_words_to_add_list,
    open_inflection_tables,
    open_sandhi_corrections,
    open_sandhi_exceptions,
    open_sandhi_ok,
    open_sandhi_rules,
    open_spelling_mistakes,
    open_variant_readings,
    remove_word_to_add,
    replace_sandhi_gui,
    reset_flags,
    sandhi_ok,
    save_gui_state,
    stasher,
    test_book_to_add,
    test_construction,
    test_family_compound,
    test_family_idioms,
    test_username,
    unstasher,
)
from gui.functions_daily_record import daily_record_update
from gui.functions_db import (
    copy_word_from_db,
    del_syns_if_pos_meaning_changed,
    delete_word,
    edit_word_in_db,
    fetch_id_or_lemma_1,
    get_family_compound_values,
    get_family_idioms_values,
    get_family_root_values,
    get_lemma_clean_list,
    get_next_ids,
    get_root_base_values,
    get_root_info,
    get_root_sign_values,
    get_sanskrit,
    get_synonyms,
    major_change_record,
    update_word_in_db,
)

from gui.functions_show_fields import (
    show_all_fields,
    show_compound_fields,
    show_root_fields,
    show_word_fields,
)
from gui.functions_tests import (
    db_internal_tests,
    individual_internal_tests,
    open_internal_tests,
)

from gui.pass2 import Pass2Data, pass2_gui, start_from_where_gui
from gui.window_layout import window_layout
from scripts.backup.backup_dpd_headwords_and_roots import backup_dpd_headwords_and_roots
from tools.bold_definitions_search import BoldDefinitionsSearchManager
from tools.fast_api_utils import (
    request_bold_def_server,
    request_dpd_server,
    start_dpd_server,
)
from tools.goldendict_tools import open_in_goldendict
from tools.missing_meanings import find_missing_meanings
from tools.paths import ProjectPaths
from tools.pos import DECLENSIONS, POS, VERBS
from tools.sandhi_contraction import SandhiContractionFinder


def main():
    pth: ProjectPaths = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    username = test_username(sg)
    pali_word_original = None
    pali_word_original2 = None
    last_word_id = None

    start_dpd_server()

    family_compound_values = get_family_compound_values(db_session)
    family_idioms_values = get_family_idioms_values(db_session)

    sandhi_finder = SandhiContractionFinder()
    sandhi_dict = sandhi_finder.get_sandhi_contractions_simple()

    with open(pth.hyphenations_dict_path) as f:
        hyphenations_dict = json.load(f)

    lemma_clean_list: list = get_lemma_clean_list(db_session)
    window = window_layout(db_session)
    daily_record_update(window, pth, "refresh", 0)

    # load the previously saved state of the gui
    try:
        saved_values, words_to_add_list = load_gui_state(pth)
        for key, value in saved_values.items():
            window[key].update(value)
        window["word_to_add"].update(words_to_add_list)
        window["words_to_add_length"].update(value=len(words_to_add_list))
    except FileNotFoundError:
        window["messages"].update(
            value="previously saved state not found. select a book to add",
            text_color="white",
        )
        words_to_add_list = []

    flags: Flags = Flags()
    archived_example_index = 0
    if username == "primary_user":
        get_next_ids(db_session, window)
    else:
        # Perform actions for other usernames
        get_next_ids(db_session, window)

    hide_list_all = [
        "sutta_to_add",
        "source_to_add",
        "field_for_id_list",
        "online_suggestion",
    ]

    while True:
        event, values = window.read()  # type: ignore

        print(f"{event}")

        if event == sg.WIN_CLOSED:
            break

        elif event == "control_q":
            close_yes_cancel = sg.popup_ok_cancel(
                "Are you sure you want to quit?", title="Quit", location=(400, 400)
            )
            if close_yes_cancel == "OK":
                break

        # tabs jumps to next field in multiline
        if event == "meaning_1_tab":
            focus = window["meaning_1"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "construction_tab":
            focus = window["construction"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "phonetic_tab":
            focus = window["phonetic"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "commentary_tab":
            focus = window["commentary"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "notes_tab":
            focus = window["notes"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "notes_italic_bold_tab":
            focus = window["notes_italic_bold"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_1_tab":
            focus = window["example_1"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_2_tab":
            focus = window["example_2"].get_next_focus()
            if focus is not None:
                focus.set_focus()

        # word to add tab
        # add book
        elif event == "book_to_add_enter" or event == "books_to_add_button":
            if test_book_to_add(values, window):
                words_to_add_list = make_words_to_add_list(
                    db_session, pth, window, values["book_to_add"]
                )

                if words_to_add_list != []:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(value=len(words_to_add_list))
                    print(values)
                    open_in_goldendict(words_to_add_list[0])
                    window["messages"].update(
                        value=f"added missing words from {values['book_to_add']}",
                        text_color="white",
                    )
                else:
                    window["messages"].update(
                        value="empty list, try again", text_color="red"
                    )

        # open word in goldendict

        elif event == "word_to_add":
            if values["word_to_add"] != []:
                open_in_goldendict(values["word_to_add"][0])
                pyperclip.copy(values["word_to_add"][0])
                # if username == "deva":
                #     request_dpd_server(values["word_to_add"][0])
                print(window["word_to_add"].get_list_values())  # type: ignore

        # sandhi ok

        elif event == "sandhi_ok":
            print(values)
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list
                )
                sandhi_ok(pth, window, values["word_to_add"][0])
                daily_record_update(window, pth, "check", values["word_to_add"][0])

                if values["word_to_add"][0] in words_to_add_list:
                    words_to_add_list.remove(values["word_to_add"][0])

                try:
                    values["word_to_add"] = [words_to_add_list[0]]
                    window["word_to_add"].update(values=words_to_add_list)
                    window["words_to_add_length"].update(value=len(words_to_add_list))
                    open_in_goldendict(words_to_add_list[0])
                except IndexError:
                    window["messages"].update(
                        value="no more words to add", text_color="red"
                    )

        # add word

        elif event == "add_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list
                )
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
                    values, window, words_to_add_list
                )
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
                    values, window, words_to_add_list
                )
                window["words_to_add_length"].update(value=len(words_to_add_list))

        # pass2
        elif (
            event == "pass2_button" or event == "pass2_button0" or event == "control_p"
        ):
            if flags.pass2_start or event == "pass2_button":
                book = values["book_to_add"]
                window["messages"].update(
                    value="loading pass2 data...", text_color="white"
                )
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
            focus = window["lemma_1"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "lemma_2_tab":
            focus = window["lemma_2"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "pos_tab":
            focus = window["pos"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "grammar_tab":
            focus = window["grammar"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "meaning_1_tab":
            focus = window["meaning_1"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "construction_tab":
            focus = window["construction"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "phonetic_tab":
            focus = window["phonetic"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "commentary_tab":
            focus = window["commentary"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_1_tab":
            focus = window["example_1"].get_next_focus()
            if focus is not None:
                focus.set_focus()
        elif event == "example_2_tab":
            focus = window["example_2"].get_next_focus()
            if focus is not None:
                focus.set_focus()

        # add word events

        if event == "get_next_id_button":
            get_next_ids(db_session, window)

        # copy lemma_1 to lemma_2
        if event == "lemma_1_tab":
            if flags.lemma_2:
                lemma_2 = re.sub(" \\d.*", "", values["lemma_1"])
                window["lemma_2"].update(value=lemma_2)
                flags.lemma_2 = False

        # test pos
        if event == "grammar":
            if values["pos"] not in POS and values["lemma_1"]:
                window["pos_error"].update(
                    value=f"'{values['pos']}' not a valid pos", text_color="red"
                )

            # add pos to grammar
            if flags.grammar and not values["grammar"]:
                if values["pos"] in VERBS:
                    window["grammar"].update(value=f"{values['pos']} of ")
                else:
                    window["grammar"].update(value=f"{values['pos']}, ")
                flags.grammar = False

        # lemma_2 masc o / nt aṃ / masc as
        if event == "pos_tab":
            if values["pos"] == "masc" and values["lemma_2"].endswith("a"):
                masc_o = re.sub("a$", "o", values["lemma_2"])
                window["lemma_2"].update(value=masc_o)
            elif values["pos"] == "nt" and values["lemma_2"].endswith("a"):
                nt_aṃ = re.sub("a$", "aṃ", values["lemma_2"])
                window["lemma_2"].update(value=nt_aṃ)
            elif values["pos"] == "masc" and values["lemma_2"].endswith("as"):
                masc_as = re.sub("as$", "ā", values["lemma_2"])
                window["lemma_2"].update(value=masc_as)
                window["grammar"].update(value="masc, mano group, ")
            # fix adjecitves ending with 'o' and 'aṃ'
            elif values["pos"] == "adj" and (
                values["lemma_2"].endswith("aṃ") or values["lemma_2"].endswith("o")
            ):
                a_adj = re.sub("(aṃ|o)$", "a", values["lemma_2"])
                window["lemma_2"].update(value=a_adj)

        if event == "derived_from":
            if flags.derived_from:
                if " of " in values["grammar"] or " from " in values["grammar"]:
                    derived_from = re.sub(
                        ".+( of | from )(.+)(,|$)", r"\2", values["grammar"]
                    )
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
                value=f"{word} added to dictionary", text_color="white"
            )
            window["add_spelling"].update(value="")

        elif event == "edit_spelling_button":
            edit_spelling(pth)

        elif event == "family_root":
            root_info = get_root_info(db_session, values["root_key"])
            window["root_info"].update(value=root_info)

        elif (
            event == "family_root" and not values["family_root"] and values["root_key"]
        ):
            if flags.family_root:
                root_key = values["root_key"]
                try:
                    FAMILY_ROOT_VALUES = get_family_root_values(db_session, root_key)
                    window["family_root"].update(values=FAMILY_ROOT_VALUES)
                    flags.family_root = False
                except UnboundLocalError as e:
                    window["messages"].update(
                        value=f"not a root. {e}", text_color="red"
                    )

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
                    value="no root_key selected", text_color="red"
                )

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
                    value="no root_key selected", text_color="red"
                )

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
                    value="no root_key selected", text_color="red"
                )

        elif event == "family_compound":
            if (
                flags.family_compound
                and not values["family_compound"]
                and not values["root_key"]
            ):
                window["family_compound"].update(values["lemma_1"])
                flags.family_compound = False
            else:
                test_family_compound(values, window, family_compound_values)

        elif event == "family_idioms":
            if (
                flags.family_idioms
                and not values["family_idioms"]
                and "comp" not in values["grammar"]
            ):
                window["family_idioms"].update(values["family_compound"])
                flags.family_idioms = False
                if values["pos"] in ["idiom", "sandhi"]:
                    window["family_compound"].update(value="")
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
                    value=f"{values['construction']}\n{lemma_clean}"
                )
                flags.construction_line2 = False

        elif event == "add_construction_enter" or event == "add_construction_button":
            new_word_to_add = values["add_construction"]
            words_to_add_list = add_to_word_to_add(
                words_to_add_list, new_word_to_add, window
            )
            window["word_to_add"].update(values=words_to_add_list)
            window["words_to_add_length"].update(value=len(words_to_add_list))

        elif event == "control_a":
            new_word_to_add = sg.popup_get_text(
                "What word would you like to add?",
                title="Add a word",
                location=(400, 400),
            )
            if new_word_to_add:
                words_to_add_list = add_to_word_to_add(
                    words_to_add_list, new_word_to_add, window
                )
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
                values["compound_type"]
                and flags.compound_construction
                and not values["compound_construction"]
            ):
                cc = make_compound_construction(values)
                window["compound_construction"].update(value=cc)
                flags.compound_construction = False

        elif event == "bold_cc_button" or event == "bold_cc_enter":
            if values["bold_cc"]:
                cc_bold = re.sub(
                    values["bold_cc"],
                    f"<b>{values['bold_cc']}</b>",
                    values["compound_construction"],
                )
                window["compound_construction"].update(value=cc_bold)
                window["bold_cc"].update(value="")

        elif (
            (
                event == "example_1"
                and flags.example_1
                and not values["example_1"]
                and values["lemma_1"]
                and values["word_to_add"]
            )
            or (
                event == "source_1"
                and flags.example_1
                and not values["example_1"]
                and values["lemma_1"]
                and values["word_to_add"]
            )
            or (
                event == "sutta_1"
                and flags.example_1
                and not values["example_1"]
                and values["lemma_1"]
                and values["word_to_add"]
            )
            or event == "another_eg_1"
        ):
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None, location=(400, 400)
                )
                if book_to_add:
                    values["book_to_add"] = book_to_add

            # if values["word_to_add"] == []:
            default_text = re.sub(r" \d.*$", "", values["lemma_1"])
            word_to_add = sg.popup_get_text(
                "What word?",
                default_text=default_text[:-1],
                title=None,
                location=(400, 400),
            )
            if word_to_add:
                values["word_to_add"] = [word_to_add]
                window["word_to_add"].update(values=[word_to_add])

            if (
                test_book_to_add(values, window)
                and values["book_to_add"]
                and values["word_to_add"]
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
                    values["bold_1"], f"<b>{values['bold_1']}</b>", values["example_1"]
                )
                window["example_1"].update(value=example_1_bold)
                window["bold_1"].update(value="")

        elif event == "example_1_lower":
            values["sutta_1"] = values["sutta_1"].lower()
            window["sutta_1"].update(values["sutta_1"])
            values["example_1"] = values["example_1"].lower()
            window["example_1"].update(values["example_1"])

        elif event == "example_1_clean":
            replace_sandhi_gui(
                values["example_1"], "example_1", sandhi_dict, hyphenations_dict, window
            )
            replace_sandhi_gui(
                values["bold_1"], "bold_1", sandhi_dict, hyphenations_dict, window
            )

        elif event == "example_1_save":
            example_save(pth, values, window, "1")

        elif event == "example_1_load":
            example_load(pth, window, "1")

        elif event == "example_1_clear":
            window["source_1"].update(value="")
            window["sutta_1"].update(value="")
            window["example_1"].update(value="")

        elif event == "example_swap":
            new_source_1 = values["source_2"]
            new_sutta_1 = values["sutta_2"]
            new_example_1 = values["example_2"]
            window["source_2"].update(value=values["source_1"])
            window["sutta_2"].update(value=values["sutta_1"])
            window["example_2"].update(value=values["example_1"])
            window["source_1"].update(value=new_source_1)
            window["sutta_1"].update(value=new_sutta_1)
            window["example_1"].update(value=new_example_1)

        elif event == "example_2_clean":
            replace_sandhi_gui(
                values["example_2"], "example_2", sandhi_dict, hyphenations_dict, window
            )
            replace_sandhi_gui(
                values["bold_2"], "bold_2", sandhi_dict, hyphenations_dict, window
            )

        elif event == "example_2_save":
            example_save(pth, values, window, "2")

        elif event == "example_2_load":
            example_load(pth, window, "2")

        elif event == "example_2_clear":
            window["source_2"].update(value="")
            window["sutta_2"].update(value="")
            window["example_2"].update(value="")

        elif event == "commentary_clean":
            replace_sandhi_gui(
                values["commentary"],
                "commentary",
                sandhi_dict,
                hyphenations_dict,
                window,
            )

        elif event == "another_eg_2":
            if not values["book_to_add"]:
                book_to_add = sg.popup_get_text(
                    "Which book?", title=None, location=(400, 400)
                )
                values["book_to_add"] = book_to_add

            default_text = re.sub(r" \d.*$", "", values["lemma_1"])
            word_to_add = sg.popup_get_text(
                "What word?",
                default_text=default_text[:-1],
                title=None,
                location=(400, 400),
            )
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
                    values["bold_2"], f"<b>{values['bold_2']}</b>", values["example_2"]
                )
                window["example_2"].update(value=example_2_bold)
                window["bold_2"].update(value="")

        elif event == "example_2_lower":
            values["sutta_2"] = values["sutta_2"].lower()
            window["sutta_2"].update(values["sutta_2"])
            values["example_2"] = values["example_2"].lower()
            window["example_2"].update(values["example_2"])

        elif event == "synonym":
            if flags.synonyms:
                synonyms = get_synonyms(
                    db_session, values["pos"], values["meaning_1"], values["lemma_1"]
                )
                window["synonym"].update(value=synonyms)
                window["messages"].update(value="synonyms updated")
                flags.synonyms = False

        elif event == "search_for":
            if not values["search_for"]:
                word_no_spaces = re.sub(r" \d.*", "", values["lemma_1"])
                window["search_for"].update(value=word_no_spaces[:-1])

        elif event == "search_for_enter" or event == "definitions_search_button":
            commentary_definitions = None
            commentary_manager = BoldDefinitionsSearchManager()
            try:
                commentary_definitions = commentary_manager.search(
                    values["search_for"], values["contains"]
                )
            except NameError as e:
                window["messages"].update(
                    value=f"turn on the definitions db! {e}", text_color="red"
                )

            if commentary_definitions:
                commentary = ""
                for c in commentary_definitions:
                    commentary += f"({c.ref_code}) {c.commentary}\n"
                commentary = commentary.rstrip("\n")
                window["commentary"].update(value=commentary)

        elif event == "bold_definitions_server":
            request_bold_def_server(values["search_for"], values["contains"], "regex")

        elif event == "notes_italic_button" or event == "notes_italic_bold_enter":
            if values["notes_italic_bold"]:
                notes_italic = re.sub(
                    values["notes_italic_bold"],
                    f"<i>{values['notes_italic_bold']}</i>",
                    values["notes"],
                )
                window["notes"].update(value=notes_italic)
                window["notes_italic_bold"].update(value="")

        elif event == "notes_bold_button":
            if values["notes_italic_bold"]:
                notes_bold = re.sub(
                    values["notes_italic_bold"],
                    f"<b>{values['notes_italic_bold']}</b>",
                    values["notes"],
                )
                window["notes"].update(value=notes_bold)
                window["notes_italic_bold"].update(value="")

        elif event == "sanskrit":
            if flags.sanskrit and not values["root_key"] and not values["sanskrit"]:
                sanskrit = get_sanskrit(db_session, values["construction"])
                window["sanskrit"].update(value=sanskrit)
                flags.sanskrit = False

        elif event == "stem":
            if flags.stem:
                add_stem_pattern(values, window)
                flags.stem = False

        # add word buttons

        elif (
            event == "Clone" or event == "word_to_clone_edit_enter" or event == "alt_c"
        ):
            if values["word_to_clone_edit"]:
                copy_word_from_db(db_session, values, window)
                window["word_to_clone_edit"].update(value="")
            else:
                window["messages"].update(value="No word to copy!", text_color="red")

        elif event == "edit_button" or event == "alt_e":
            if values["word_to_clone_edit"]:
                pali_word_original = edit_word_in_db(db_session, values, window)
                pali_word_original2 = deepcopy(pali_word_original)
                open_in_goldendict(values["word_to_clone_edit"])
                window["word_to_clone_edit"].update(value="")
                flags = show_all_fields(
                    values,
                    window,
                    flags,
                    username,
                    hide_list_all,
                )

            else:
                window["messages"].update(value="No word to edit!", text_color="red")

        elif event == "open_last_word":
            if last_word_id:
                values["word_to_clone_edit"] = last_word_id
            else:
                values["word_to_clone_edit"] = str(int(values["id"]) - 1)
            if values["word_to_clone_edit"]:
                pali_word_original = edit_word_in_db(db_session, values, window)
                pali_word_original2 = deepcopy(pali_word_original)
                open_in_goldendict(values["word_to_clone_edit"])
                window["word_to_clone_edit"].update(value="")
            else:
                window["messages"].update(value="No word to edit!", text_color="red")

        # gui buttons

        elif event == "clear_button" or event == "control_l":
            clear_errors(window)
            clear_values(values, window, username)
            if username == "primary_user":
                get_next_ids(db_session, window)
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
            flags = individual_internal_tests(pth, sg, window, values, flags, username)

            # spell checks
            field = "meaning_1"
            error_field = "meaning_1_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)
            if flags.spelling_ok is False:
                continue

            field = "meaning_lit"
            error_field = "meaning_lit_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)
            if flags.spelling_ok is False:
                continue

            field = "meaning_2"
            error_field = "meaning_2_error"
            flags = check_spelling(pth, field, error_field, values, window, flags)
            if flags.spelling_ok is False:
                continue

            # check allowable characters
            error_dict = test_allowable_characters_gui(values)
            for column, test_value in error_dict.items():
                if column != "origin":
                    if test_value:
                        window[f"{column}_error"].update(
                            value=test_value, text_color="red"
                        )
                        window["messages"].update(
                            value="fix bad characters", text_color="red"
                        )
                        window["update_db_button1"].update(button_color="red")
                        flags.tested = False
                    else:
                        window[f"{column}_error"].update(
                            value="", text_color="darkgray"
                        )
                        window["update_db_button1"].update(button_color="steel blue")

        elif event == "open_tests_button":
            open_internal_tests(pth)

        elif event == "open_sanskrit_roots_button":
            subprocess.Popen(["libreoffice", pth.root_families_sanskrit_path])

        elif event == "update_sandhi_button":
            sandhi_dict = sandhi_finder.update_contractions()

        elif event == "refresh_db_session_button":
            db_session.close()
            db_session = get_db_session(pth.dpd_db_path)

        elif event == "update_db_button1" or event == "control_u":
            if not flags.tested:
                window["messages"].update(value="test first!", text_color="red")

            elif not flags.spelling_ok:
                yes_no = sg.popup_yes_no(
                    "There are spelling mistakes. Are you sure you want to continue?",
                    location=(400, 400),
                    modal=True,
                )
                if yes_no == "Yes":
                    flags.spelling_ok = True
                else:
                    continue

            last_button = display_summary(values, window, sg, pali_word_original2)

            if last_button == "ok_button":
                success, action = update_word_in_db(pth, db_session, window, values)

                if success:
                    # major_change_record
                    if flags.change_meaning:
                        major_change_record(pth, db_session, values)
                    last_word_id = values["id"]
                    del_syns_if_pos_meaning_changed(
                        db_session, values, pali_word_original2
                    )
                    clear_errors(window)
                    clear_values(values, window, username)
                    if username == "primary_user":
                        get_next_ids(db_session, window)
                    else:
                        # Perform actions for other usernames
                        get_next_ids(db_session, window)
                    reset_flags(flags)
                    remove_word_to_add(values, window, words_to_add_list)
                    window["words_to_add_length"].update(value=len(words_to_add_list))

            # add missing meanings
            example_1_2_commentary = f"""{values["example_1"]} {values["example_2"]} {values["commentary"]}"""
            missing_meanings = find_missing_meanings(db_session, example_1_2_commentary)
            if missing_meanings:
                missing_meanings_reduced = [
                    i for i in missing_meanings if i not in words_to_add_list
                ]
                words_to_add_list.extend(missing_meanings_reduced)
                window["word_to_add"].update(values=words_to_add_list)

        elif event == "update_db_button2":
            tests_failed = None
            if not flags.tested:
                tests_failed = sg.popup_ok_cancel(
                    "Tests have failed. Are you sure you want to add to db?",
                    title="Error",
                    location=(400, 400),
                )
            if tests_failed or flags.tested:
                last_button = display_summary(values, window, sg, pali_word_original2)
                if last_button == "ok_button":
                    success, action = update_word_in_db(pth, db_session, window, values)
                    if success:
                        book_to_add = values["book_to_add"]
                        compare_differences(
                            book_to_add, pth, values, sg, pali_word_original2, action
                        )
                        clear_errors(window)
                        clear_values(values, window, username)
                        if username == "primary_user":
                            get_next_ids(db_session, window)
                        else:
                            # Perform actions for other usernames
                            get_next_ids(db_session, window)
                        reset_flags(flags)
                        remove_word_to_add(values, window, words_to_add_list)
                        window["words_to_add_length"].update(
                            value=len(words_to_add_list)
                        )

                        pyperclip.copy(values["lemma_1"])
                        open_in_goldendict(values["lemma_1"])

        elif event == "open_corrections_button":
            edit_corrections(pth)

        elif event == "debug_button":
            print(f"{values}")

        elif event == "stash_button" or event == "alt_s":
            stasher(pth, values, window)

        elif event == "unstash_button" or event == "alt_u":
            if username == "deva":
                if sg.popup_yes_no("unshash?") == "Yes":
                    unstasher(pth, window)
            else:
                unstasher(pth, window)

        elif event == "split_button":
            lemma_1_old, lemma_1_new = increment_lemma_1(values)
            window["lemma_1"].update(value=lemma_1_old)
            values["lemma_1"] = lemma_1_old
            stasher(pth, values, window)
            get_next_ids(db_session, window)
            window["lemma_1"].update(value=lemma_1_new)
            reset_flags(flags)

            # clear these fields
            clear_fields = [
                "messages",
                "commentary",
                "synonym",
                "variant",
                "notes",
                "source_1",
                "sutta_1",
                "example_1",
                "source_2",
                "sutta_2",
                "example_2",
                "antonym",
                "synonym",
                "variant",
            ]
            for c in clear_fields:
                window[c].update(value="")

        elif event == "html_summary_button":
            request_dpd_server(values["id"])

        elif event == "save_state_button" or event == "control_s":
            save_gui_state(pth, values, words_to_add_list)
            window["messages"].update(value="saved gui state", text_color="green")

        elif event == "delete_button":
            row_id = values["id"]
            lemma_1 = values["lemma_1"]
            yes_no = sg.popup_yes_no(
                f"Are you sure you want to delete {row_id} {lemma_1}?",
                location=(400, 400),
                modal=True,
            )
            if yes_no == "Yes":
                success = delete_word(pth, db_session, values, window)
                if success:
                    clear_errors(window)
                    clear_values(values, window, username)
                    if username == "primary_user":
                        get_next_ids(db_session, window)
                    else:
                        # Perform actions for other usernames
                        get_next_ids(db_session, window)
                    reset_flags(flags)
                    window["messages"].update(
                        value=f"{row_id} '{lemma_1}' deleted", text_color="white"
                    )

        elif event == "save_and_close_button":
            window["messages"].update(value="backing up db to csvs", text_color="white")
            if username == "primary_user":
                backup_dpd_headwords_and_roots(pth)

                save_gui_state(pth, values, words_to_add_list)
                window["messages"].update(value="saved gui state", text_color="green")
            break

        elif event == "load_example_button":
            load_example_data = json.loads(pth.load_example_dump.read_text())
            load_eg_id, load_eg_source, load_eg_sutta, load_eg_example = (
                load_example_data
            )
            values["word_to_clone_edit"] = str(load_eg_id)
            pali_word_original = edit_word_in_db(db_session, values, window)
            pali_word_original2 = deepcopy(pali_word_original)
            open_in_goldendict(values["word_to_clone_edit"])
            flags = show_all_fields(
                values,
                window,
                flags,
                username,
                hide_list_all,
            )
            window["source_1"].update(value=load_eg_source)
            window["sutta_1"].update(value=load_eg_sutta)
            window["example_1"].update(value=load_eg_example)

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

        # show / hide fields

        elif event == "show_fields_all":
            flags = show_all_fields(values, window, flags, username, hide_list_all)

        elif event == "show_fields_root":
            flags = show_root_fields(values, window, hide_list_all, username, flags)

        elif event == "show_fields_compound":
            flags = show_compound_fields(values, window, hide_list_all, username, flags)

        elif event == "show_fields_word":
            flags = show_word_fields(values, window, hide_list_all, username, flags)

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

        # flags for majore changes

        elif event == "meaning_1_majore_change_checkbox":
            flags.change_meaning = values["meaning_1_majore_change_checkbox"]

        # edit word in DPD
        elif event == "dpd_edit_word":
            if values["word_to_add"] == []:
                window["messages"].update(value="nothing selected", text_color="red")
            else:
                words_to_add_list = remove_word_to_add(
                    values, window, words_to_add_list
                )
                window["words_to_add_length"].update(value=len(words_to_add_list))
                window["tab_edit_dpd"].select()  # type: ignore
                window["word_to_clone_edit"].update(values["word_to_add"][0])

        # length of examples must be less than 300

        if len(values["example_1"]) > 280:
            window["example_1"].update(text_color="red")

        elif len(values["example_1"]) <= 280:
            window["example_1"].update(text_color="darkgray")

        if len(values["example_2"]) > 280:
            window["example_2"].update(text_color="red")

        elif len(values["example_2"]) <= 280:
            window["example_2"].update(text_color="darkgray")

        if len(values["example_1"]) > 280 or len(values["example_2"]) > 280:
            window["update_db_button1"].update(button_color="red")
        else:
            window["update_db_button1"].update(button_color="steel blue")

        # test db tab

    window.close()


if __name__ == "__main__":
    main()
