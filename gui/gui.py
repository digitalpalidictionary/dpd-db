#!/usr/bin/env python3.11
import PySimpleGUI as sg
import re
import pandas as pd


from rich import print

from window_layout import window_layout
from db_helpers import add_word_to_db
from db_helpers import update_word_in_db
from db_helpers import get_next_ids
from db_helpers import dpd_values_list
from db_helpers import get_family_root_values
from db_helpers import get_root_sign_values
from db_helpers import get_root_base_values
from db_helpers import get_synonyms
from db_helpers import get_sanskrit

from functions.get_paths import get_paths
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
from functions.find_sutta_example import find_sutta_example
from functions.find_commentary_defintions import find_commentary_defintions
from functions.run_internal_tests import run_internal_tests
from functions.open_internal_tests import open_internal_tests
from functions.clear_errors import clear_errors
from functions.add_stem_pattern import add_stem_pattern
# from functions.check_spelling import check_spelling

from tools.pos import DECLENSIONS, VERBS
# sg.main_sdk_help()


def main():
    pth = get_paths()
    # definitions_df = pd.read_csv(pth.defintions_csv_path, sep="\t")
    window = window_layout()

    pali_2_flag = True
    grammar_flag = True
    derived_from_flag = True
    family_root_flag = True
    root_sign_flag = True
    root_base_flag = True
    construction_flag = True
    suffix_flag = True
    compound_construction_flag = True
    synoyms_flag = True
    commentary_flag = True
    sanskrit_flag = True
    example_1_flag = True
    stem_flag = True

    while True:
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
            if pali_2_flag:
                window["pali_2"].update(f"{values['pali_1']}")
                pali_2_flag = False

        if event == "grammar":
            if grammar_flag:
                if values["pos"] in VERBS:
                    window["grammar"].update(f"{values['pos']} of ")
                else:
                    window["grammar"].update(f"{values['pos']}, ")
                grammar_flag = False

        # comp in grammar
        # sections = [
        #     "pali_1", "pali_2", "pos", "grammar", "neg", "plus_case",
        #     "meaning_1", "family_compound", "construction",
        #     "compound_type", "compound_construction", "antonym",
        #     "synonym", "variant", "commentary"]

        # root_sections = [
        #     "verb", "root_key", "family_root", "root_sign"]

        # if re.findall(r"\bcomp\b", values["grammar"]) != []:
        #     for section in root_sections:
        #         window[f"{section}"].update(visible=False)

        # else:
        #     for section in root_sections:
        #         window[f"{section}"].update(visible=True)

            # for section in sections:
            #     if "Input" in str(type[window[f"{section}"]]):
            #         window[f"{section}"].update(background_color="black")
            #         window[f"{section}"].Widget.configure(
            #             highlightcolor='black', highlightthickness=2)


        if event == "derived_from":
            if derived_from_flag:
                if " of " in values["grammar"] or " from " in values["grammar"]:
                    derived_from = re.sub(
                        ".+( of | from )(.+)(,|$)", r"\2", values["grammar"])
                    window["derived_from"].update(derived_from)
                    derived_from_flag = False
        
        if event == "meaning_1":
            field = "meaning_1_error"
            # check_spelling(field, values, window)

        if event == "family_root" and values["root_key"] != "":
            if family_root_flag:
                root_key = values["root_key"]
                FAMILY_ROOT_VALUES = get_family_root_values(root_key)
                window["family_root"].update(values=FAMILY_ROOT_VALUES)
                family_root_flag = False

        if event == "root_sign":
            if root_sign_flag:
                root_key = values["root_key"]
                ROOT_SIGN_VALUES = get_root_sign_values(root_key)
                window["root_sign"].update(values=ROOT_SIGN_VALUES)
                root_sign_flag = False

        if event == "root_base":
            if root_base_flag:
                root_key = values["root_key"]
                ROOT_BASE_VALUES = get_root_base_values(root_key)
                window["root_base"].update(values=ROOT_BASE_VALUES)
                root_base_flag = False

        if event == "construction":
            if construction_flag:
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

                family = re.sub("√", "", family)
                window["construction"].update(f"{neg}{family} + ")
                construction_flag = False

        if event == "derivative":
            print("hello")
            "ptp" in values["grammar"]
            if "ptp" in values["grammar"]:
                window["derivative"].update("kicca")

        if event == "suffix":
            if suffix_flag and values["pos"] in DECLENSIONS:
                suffix = re.sub(r".+ \+ ", "", values["construction"])
                window["suffix"].update(suffix)
                suffix_flag = False

        if event == "compound_construction":
            if compound_construction_flag:
                window["compound_construction"].update(values["construction"])
                compound_construction_flag = False

        if ((event == "example_1" and example_1_flag) or
            (event == "source_1" and example_1_flag) or
            (event == "sutta_1" and example_1_flag) or
                event == "another_eg_1"):
            sutta_sentences = find_sutta_example(sg, values)
            window["source_1"].update(sutta_sentences["source_1"])
            window["sutta_1"].update(sutta_sentences["sutta_1"])
            window["example_1"].update(sutta_sentences["example_1"])
            example_1_flag = False

        if event == "bold_1_button":
            example_1_bold = re.sub(
                values["bold_1"],
                f"<b>{values['bold_1']}</b>",
                values["example_1"])
            window["example_1"].update(example_1_bold)
            window["bold_1"].update("")

        if event == "bold_2_button":
            example_2_bold = re.sub(
                values["bold_2"],
                f"<b>{values['bold_2']}</b>",
                values["example_2"])
            window["example_2"].update(example_2_bold)
            window["bold_2"].update("")

        if event == "another_eg_2":
            sutta_sentences = find_sutta_example(sg, values)
            window["source_2"].update(sutta_sentences["source_1"])
            window["sutta_2"].update(sutta_sentences["sutta_1"])
            window["example_2"].update(sutta_sentences["example_1"])
            example_1_flag = False

        if event == "synonym":
            if synoyms_flag:
                synoyms = get_synonyms(values["pos"], values["meaning_1"])
                window["synonym"].update(synoyms)
                synoyms_flag = False

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
            if sanskrit_flag and re.findall(r"\bcomp\b", values["grammar"]) != []:
                sanskrit = get_sanskrit(values["construction"])
                window["sanskrit"].update(sanskrit)
                sanskrit_flag = False
        
        if event == "stem":
            if stem_flag:
                add_stem_pattern(values, window)
                stem_flag = False

        # add word buttons

        if event == "Copy" or event == "word_to_copy_enter":
            values, window = copy_word_from_db(sg, values, window)

        if event == "Clear":
            clear_errors(window)
            for value in values:
                if value in dpd_values_list:
                    window[value].update("")

            id, user_id = get_next_ids()
            window["id"].update(id)
            window["user_id"].update(user_id)
            window["origin"].update("pass1")

            pali_2_flag = True
            grammar_flag = True
            derived_from_flag = True
            family_root_flag = True
            root_sign_flag = True
            root_base_flag = True
            construction_flag = True
            suffix_flag = True
            compound_construction_flag = True
            synoyms_flag = True
            commentary_flag = True
            sanskrit_flag = True
            example_1_flag = True
            stem_flag = True

        if event == "test_internal":
            clear_errors(window)
            run_internal_tests(sg, window, values)
            # open_internal_tests()

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


# !!! pin keeps an element in place when it gets hidden and shown again !!!

