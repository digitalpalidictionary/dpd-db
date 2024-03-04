"""Functions related to the GUI."""

import re
import csv
import os
import shutil

import subprocess
import textwrap
import pickle
import configparser
from typing import Optional, Tuple, List

from spellchecker import SpellChecker
from aksharamukha import transliterate
from rich import print
from nltk import word_tokenize

from db.models import DpdHeadwords
from functions_db import make_all_inflections_set
from functions_db import values_to_pali_word

from tools.addition_class import Addition
from tools.bold_definitions_search import search_bold_defintions
from tools.configger import config_test_option
from tools.configger import config_update
from tools.configger import config_test
from tools.configger import config_read
from tools.cst_sc_text_sets import make_cst_text_list
from tools.cst_sc_text_sets import make_sc_text_list
from tools.pali_text_files import cst_texts
from tools.pali_alphabet import pali_alphabet
from tools.pos import INDECLINABLES
from tools.source_sutta_example import find_source_sutta_example

# nltk.download('punkt')



class Flags:
    def __init__(self):
        self.show_fields = True
        self.lemma_2 = True
        self.grammar = True
        self.derived_from = True
        self.family_root = True
        self.root_sign = True
        self.root_base = True
        self.family_compound = True
        self.family_idioms = True
        self.construction = True
        self.construction_line2 = True
        self.suffix = True
        self.compound_construction = True
        self.synoyms = True
        self.commentary = True
        self.sanskrit = True
        self.example_1 = True
        self.example_2 = False
        self.stem = True
        self.tested = False
        self.test_next = False
        self.spelling_ok = False
        self.pass2_start = True


def reset_flags(flags):
    flags.show_fields = True
    flags.lemma_2 = True
    flags.grammar = True
    flags.derived_from = True
    flags.family_root = True
    flags.root_sign = True
    flags.root_base = True
    flags.family_compound = True
    flags.construction = True
    flags.construction_line2 = True
    flags.suffix = True
    flags.compound_construction = True
    flags.synoyms = True
    flags.commentary = True
    flags.sanskrit = True
    flags.example_1 = True
    flags.example_2 = False
    flags.stem = True
    flags.tested = False
    flags.test_next = False
    # flags.pass2_start must remain for the session


def add_sandhi_correction(pth, window, values: dict) -> None:
    sandhi_to_correct = values["sandhi_to_correct"]
    sandhi_correction = values["sandhi_correction"]

    if not sandhi_to_correct or not sandhi_correction:
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    elif " + " not in sandhi_correction:
        window["messages"].update(
            "no plus sign in sandhi correction!", text_color="red")

    else:

        with open(
                pth.manual_corrections_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([sandhi_to_correct, sandhi_correction])
        
        # also add to sandhi ok
        with open(
                pth.sandhi_ok_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([sandhi_to_correct])
        
        window["messages"].update(
            f"{sandhi_to_correct} > {sandhi_correction} added to corrections", text_color="white")
        window["sandhi_to_correct"].update("")
        window["sandhi_correction"].update("")


def open_sandhi_corrections(pth):
    subprocess.Popen(
        ["code", pth.manual_corrections_path])


def add_sandhi_rule(pth, window, values: dict) -> None:
    chA = values["chA"]
    chB = values["chB"]
    ch1 = values["ch1"]
    ch2 = values["ch2"]
    example = values["example"]
    usage = values["usage"]

    if (not chA or not chB or (not ch1 and not ch2)):
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    elif "'" not in example:
        window["messages"].update(
            "use an apostrophe in the example!", text_color="red")

    else:

        with open(pth.sandhi_rules_path, "r") as f:
            reader = csv.reader(f, delimiter="\t")

            for row in reader:
                print(row)
                if row[0] == chA and row[1] == chB and row[2] == ch1 and row[3] == ch2:
                    window["messages"].update(
                        f"{row[0]}-{row[1]} {row[2]}-{row[3]} {row[4]} {row[5]} already exists!", text_color="red")
                    break
            else:
                with open(
                        pth.sandhi_rules_path, mode="a", newline="") as file:
                    writer = csv.writer(file, delimiter="\t")
                    writer.writerow([chA, chB, ch1, ch2, example, usage])
                    window["messages"].update(
                        f"{chA}-{chB} {ch1}-{ch2} {example} {usage} added to rules!", text_color="white")
                    window["chA"].update("")
                    window["chB"].update("")
                    window["ch1"].update("")
                    window["ch2"].update("")
                    window["example"].update("")
                    window["usage"].update("")


def open_sandhi_rules(pth):
    subprocess.Popen(
        ["code", pth.sandhi_rules_path])


def add_spelling_mistake(pth, window, values: dict) -> None:
    spelling_mistake = values["spelling_mistake"]
    spelling_correction = values["spelling_correction"]

    if not spelling_mistake or not spelling_correction:
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:

        with open(
                pth.spelling_mistakes_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([spelling_mistake, spelling_correction])
            window["messages"].update(
                f"{spelling_mistake} > {spelling_correction} added to spelling mistakes", text_color="white")
            window["spelling_mistake"].update("")
            window["spelling_correction"].update("")


def open_spelling_mistakes(pth):
    subprocess.Popen(
        ["code", pth.spelling_mistakes_path])


def add_variant_reading(pth, window, values: dict) -> None:
    variant_reading = values["variant_reading"]
    main_reading = values["main_reading"]

    if not variant_reading or not main_reading:
        window["messages"].update(
            "you're shooting blanks!", text_color="red")

    else:
        with open(
                pth.variant_readings_path, mode="a", newline="") as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([variant_reading, main_reading])
            window["messages"].update(
                f"{variant_reading} > {main_reading} added to variant readings", text_color="white")
            window["variant_reading"].update("")
            window["main_reading"].update("")


def open_variant_readings(pth):
    subprocess.Popen(
        ["code", pth.variant_readings_path])


def open_sandhi_ok(pth):
    subprocess.Popen(
        ["code", pth.sandhi_ok_path])


def open_sandhi_exceptions(pth):
    subprocess.Popen(
        ["code", pth.sandhi_exceptions_path])


def add_stem_pattern(values, window):
    pos = values["pos"]
    grammar = values["grammar"]
    lemma_1 = values["lemma_1"]
    lemma_1_clean = re.sub(r"\s\d.*$", "", lemma_1)

    if pos == "adj":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a adj")
        if lemma_1_clean.endswith("ī"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ī adj")
        if lemma_1_clean.endswith("ant"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("ant adj")
        if lemma_1_clean.endswith("u"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("u adj")
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i adj")
        if lemma_1_clean.endswith("ū"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ū adj")
        if lemma_1_clean.endswith("aka"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("aka adj")

    elif pos == "masc":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a masc")
        if lemma_1_clean.endswith("ī"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ī masc")
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i masc")
        if lemma_1_clean.endswith("u"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("u masc")
        if lemma_1_clean.endswith("ar"):
            window["stem"].update(lemma_1_clean[:-2])
            window["pattern"].update("ar masc")
        if lemma_1_clean.endswith("as"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("as masc")
        if lemma_1_clean.endswith("ū"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ū masc")
        if lemma_1_clean.endswith("ant"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("ant masc")
        if lemma_1_clean.endswith("ā"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a masc pl")
        if lemma_1_clean.endswith("as"):
            window["stem"].update(lemma_1_clean[:-2])
            window["pattern"].update("as masc")

    elif pos == "fem":
        if lemma_1_clean.endswith("ā"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ā fem")
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i fem")
        if lemma_1_clean.endswith("ī"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ī fem")
        if lemma_1_clean.endswith("u"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("u fem")
        if lemma_1_clean.endswith("ar"):
            window["stem"].update(lemma_1_clean[:-2])
            window["pattern"].update("ar fem")
        if lemma_1_clean.endswith("ū"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ū fem")
        if lemma_1_clean.endswith("mātar"):
            window["stem"].update(lemma_1_clean[:-5])
            window["pattern"].update("mātar fem")

    elif pos == "nt":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a nt")
        if lemma_1_clean.endswith("u"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("u nt")
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i nt")

    elif pos == "card":
        if "x pl" in grammar:
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a1 card")
        if "nt sg" in grammar:
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a2 card")
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i card")
        if lemma_1_clean.endswith("koṭi"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i2 card")
        if lemma_1_clean.endswith("ā"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ā card")

    elif pos == "ordin":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a ordin")

    elif pos == "pp":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a pp")

    elif pos == "prp":
        if lemma_1_clean.endswith("anta"):
            window["stem"].update(lemma_1_clean[:-4])
            window["pattern"].update("anta prp")
        if lemma_1_clean.endswith("enta"):
            window["stem"].update(lemma_1_clean[:-4])
            window["pattern"].update("enta prp")
        if lemma_1_clean.endswith("onta"):
            window["stem"].update(lemma_1_clean[:-4])
            window["pattern"].update("onta prp")
        if lemma_1_clean.endswith("māna"):
            window["stem"].update(lemma_1_clean[:-4])
            window["pattern"].update("māna prp")
        elif lemma_1_clean.endswith("āna"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("āna prp")

    elif pos == "ptp":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a ptp")

    elif pos == "pron":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a pron")

    elif pos == "pr":
        if lemma_1_clean.endswith("ati"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("ati pr")
        if lemma_1_clean.endswith("eti"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("eti pr")
        if lemma_1_clean.endswith("oti"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("oti pr")
        if lemma_1_clean.endswith("āti"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("āti pr")

    elif pos == "aor":
        if lemma_1_clean.endswith("i"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("i aor")
        if lemma_1_clean.endswith("esi"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("esi aor")
        if lemma_1_clean.endswith("āsi"):
            window["stem"].update(lemma_1_clean[:-3])
            window["pattern"].update("āsi aor")

    elif pos == "perf":
        if lemma_1_clean.endswith("a"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("a perf")

    elif pos == "imperf":
        if lemma_1_clean.endswith("ā"):
            window["stem"].update(lemma_1_clean[:-1])
            window["pattern"].update("ā imperf")

    elif pos in INDECLINABLES:
        window["stem"].update("-")
        window["pattern"].update("")

# !!! add all the plural forms !!!





def check_spelling(pth, field, error_field, values, window, flags) -> Flags:

    spell = SpellChecker(language='en')
    spell.word_frequency.load_text_file(str(pth.user_dict_path))

    sentence = values[field].replace("-", " ")
    words = word_tokenize(sentence)

    misspelled = spell.unknown(words)

    candidates = ""
    for word in misspelled:
        candidates = spell.candidates(word)
        window[error_field].update(f"{candidates}")
    
    if misspelled:
        window[field].update(text_color="red")
        flags.spelling_ok = False
        return flags
    else:
        window[field].update(text_color="darkgray")
        window[error_field].update("")
        flags.spelling_ok = True
        return flags


def add_spelling(pth, word):
    with open(pth.user_dict_path, "a") as f:
        f.write(f"{word}\n")


def edit_spelling(pth):
    subprocess.Popen(
        ["code", pth.user_dict_path])


def clear_errors(window):
    error_elements = [
        e for e in window.element_list()
        if hasattr(e, "key") and isinstance(e.key, str) and "error" in e.key]
    for e in error_elements:
        window[e.key].update("")


def clear_values(values, window, username):
    from functions_db import dpd_values_list
    if username == "primary_user":
        origin = "pass2"
    elif username == "deva":
        origin = "dps"
    else:
        origin = "new_user"
    for value in values:
        if value in dpd_values_list:
            window[value].update("")
    window["family_root"].update(values=[])
    window["root_sign"].update(values=[])
    window["root_base"].update(values=[])
    window["origin"].update(origin)
    window["root_info"].update("")
    window["search_for"].update("")


def find_commentary_defintions(sg, values, db_session):

    config = load_gui_config()

    # Get screen width and height
    screen_width, screen_height = sg.Window.get_screen_size()

    # Calculate width and height of the screen
    window_width = int(screen_width * config["screen_fraction_width"])
    window_height = int(screen_height * config["screen_fraction_height"])
    
    search_results = search_bold_defintions(
        db_session, values["search_for"], values["contains"])

    layout_elements = []
    layout_elements.append(
        [
            sg.Button(
                "Add Commentary Definition", key="add_button_1"),
            sg.Button(
                "Cancel", key="cancel_1")
        ]
    )

    if len(search_results) < 50:
        layout_elements.append(
            [sg.Text(f"{len(search_results)} results ")])
    else:
        layout_elements.append(
            [sg.Text("dispalying the first 50 results. \
                please refine your search")])

    for count, r in enumerate(search_results):
        if count >= 50:
            break
        else:
            try:
                commentary_clean = r.commentary.replace("<b>", "<").replace("</b>", ">")
                commentary_clean = textwrap.fill(commentary_clean, 150)

                layout_elements.append(
                    [
                        sg.Checkbox(f"{count}.", key=count),
                        sg.Text(r.ref_code),
                        sg.Text(r.bold, text_color="white"),
                    ]
                )

                # FIXME how to add actual bold text in pysimplegui?

                layout_elements.append(
                    [
                        sg.Text(
                            commentary_clean, size=(80, None),
                            text_color="lightgray"),
                    ],
                )
            except Exception:
                layout_elements.append([sg.Text("no results")])

    layout_elements.append([
        sg.Button(
            "Add Commentary Definition", key="add_button_2"),
        sg.Button(
            "Cancel", key="cancel_2")
        ])

    layout = [
        [
            [
                sg.Column(
                    layout=layout_elements, key="results",
                    expand_y=True, expand_x=True,
                    scrollable=True, vertical_scroll_only=True
                )
            ],
        ]
    ]

    window = sg.Window(
        "Find Commentary Defintions",
        layout,
        resizable=True,
        size=(window_width, window_height),
        finalize=True
    )

    while True:
        event, values = window.read()
        if event == "Close" or event == sg.WIN_CLOSED:
            break

        if event == "add_button_1" or event == "add_button_2":
            return_results = []
            number = 0
            for value in values:
                if values[value]:
                    number = int(value)
                    return_results += [search_results[number]]

            window.close()
            return return_results

        if event == "cancel_1" or event == "cancel_2":
            window.close()

    window.close()


def transliterate_xml(xml):
    """transliterate from devanagari to roman"""
    xml = transliterate.process("autodetect", "IASTPali", xml)
    if xml is None:
        # Handle the error, perhaps by raising an exception or returning a default value.
        raise ValueError("Failed to transliterate XML.")
    xml = xml.replace("ü", "u")
    xml = xml.replace("ï", "i")
    return xml


def find_sutta_example(pth, sg, window, values: dict) -> Optional[Tuple[str, str, str]]:

    config = load_gui_config()

    # Get screen width and height
    screen_width, screen_height = sg.Window.get_screen_size()

    # Calculate width and height of the screen
    window_width = int(screen_width * config["screen_fraction_width"])
    window_height = int(screen_height * config["screen_fraction_height"])

    book = values["book_to_add"]
    text_to_find = values["word_to_add"][0]
    sutta_examples = find_source_sutta_example(pth, book, text_to_find)

    sentences_list = [sentence[2] for sentence in sutta_examples]

    layout_elements = []
    layout_elements.append([
        sg.Button(
            "Add Sutta Example", key="add_button_1"),
        sg.Button(
            "Cancel", key="cancel_1")
    ])

    layout_elements.extend([
        [
            sg.Radio(
                "", "sentence",
                key=f"{i}",
                text_color="lightblue",
                pad=((0, 10), 5)),
            sg.Multiline(
                sentences_list[i],
                wrap_lines=True,
                auto_size_text=True,
                size=(76, 2),
                text_color="lightgray",
                no_scrollbar=True,
            )
        ]
        for i in range(len(sentences_list))
    ])

    layout_elements.append([
        sg.Button(
            "Add Sutta Example", key="add_button_2"),
        sg.Button(
            "Cancel", key="cancel_2")
    ])

    layout = [[
        [
            sg.Column(
                layout=layout_elements, key="results",
                expand_y=True, expand_x=True,
                scrollable=True, vertical_scroll_only=True
            )
        ],
    ]]

    window = sg.Window(
        "Find Sutta Examples",
        layout,
        resizable=True,
        size=(window_width, window_height),
        finalize=True
    )

    while True:
        event, values = window.read()

        if event == "Close" or event == sg.WIN_CLOSED:
            break

        if event == "add_button_1" or event == "add_button_2":
            number = 0
            for value in values:
                if values[value] is True:
                    number = int(value)

            if sutta_examples != []:
                window.close()
                return sutta_examples[number]
            else:
                window.close()
                return None

        if event == "cancel_1" or event == "cancel_2":
            window.close()

    window.close()

    # else:
    #     window["messages"].update("book code not found", text_color="red")


def clean_example(text):
    text = text.lower()
    text = text.replace("‘", "")
    text = text.replace(" – ", ", ")
    text = text.replace("’", "")
    text = text.replace("…pe॰…", " ... ")
    text = text.replace(";", ",")
    text = text.replace("  ", " ")
    text = text.replace("..", ".")
    text = text.replace(" ,", ",")

    return text


def clean_gatha(text):
    text = clean_example(text)
    text = text.replace(", ", ",\n")
    text = text.strip()
    return text


def find_gathalast(p, example):

    while p["rend"] != "gathalast":
        p = p.next_sibling
        if p.text == "\n":
            pass
        elif p["rend"] == "gatha2":
            example += p.text
        elif p["rend"] == "gatha3":
            example += p.text
        elif p["rend"] == "gathalast":
            example += p.text
        p = p.next_sibling


def test_book_to_add(values, window):
    """Test if book is in cst texts."""
    book = values["book_to_add"]
    if book in cst_texts:
        window["messages"].update(
            f"adding {book} ...", text_color="white")
        window.refresh()
        return True
    else:
        window["messages"].update(
            f"{book} invalid book code", text_color="red")
        return False


def make_words_to_add_list(db_session, pth, __window__, book: str) -> list:
    cst_text_list = make_cst_text_list(pth, [book])
    sc_text_list = make_sc_text_list(pth, [book])
    original_text_list = cst_text_list + sc_text_list

    sp_mistakes_list = make_sp_mistakes_list(pth)
    variant_list = make_variant_list(pth)
    sandhi_ok_list = make_sandhi_ok_list(pth)
    all_inflections_set = make_all_inflections_set(db_session)

    text_set = set(cst_text_list) | set(sc_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))
    print(f"words_to_add: {len(text_list)}")

    with open(f"temp/{book}.tsv", "w") as f:
        for i in text_list:
            f.write(f"{i}\n")

    return text_list


def make_sp_mistakes_list(pth):

    with open(pth.spelling_mistakes_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sp_mistakes_list = [row[0] for row in reader]

    print(f"sp_mistakes_list: {len(sp_mistakes_list)}")
    return sp_mistakes_list


def make_variant_list(pth):
    with open(pth.variant_readings_path) as f:
        reader = csv.reader(f, delimiter="\t")
        variant_list = [row[0] for row in reader]

    print(f"variant_list: {len(variant_list)}")
    return variant_list


def make_sandhi_ok_list(pth):
    with open(pth.sandhi_ok_path) as f:
        reader = csv.reader(f, delimiter="\t")
        sandhi_ok_list = [row[0] for row in reader]

    print(f"sandhi_ok_list: {len(sandhi_ok_list)}")
    return sandhi_ok_list


def open_inflection_tables(pth):
    subprocess.Popen(
        ["libreoffice", pth.inflection_templates_path])


def sandhi_ok(pth, window, word,):
    with open(pth.sandhi_ok_path, "a", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([word])
    window["messages"].update(f"{word} added", text_color="white")


def display_summary(values, window, sg, pali_word_original2):
    from functions_db import dpd_values_list

    # Assuming pali_word_original2 is a dictionary with the original values
    if pali_word_original2:
        original_values = pali_word_original2.__dict__
    else:
        # Handle the case when it's None, perhaps:
        original_values = {}

    summary = []
    for value in values:
        if value in dpd_values_list:
            if values[value]:
                # Check if the value is changed
                color = 'yellow' if str(original_values.get(value)) != str(values[value]) else 'white'

                if len(values[value]) < 40:
                    summary += [[
                        value, values[value], color
                    ]]
                else:
                    wrapped_lines = textwrap.wrap(values[value], width=40)
                    summary += [[value, wrapped_lines[0], color]]
                    for wrapped_line in wrapped_lines:
                        if wrapped_line != wrapped_lines[0]:
                            summary += [["", wrapped_line, color]]

                print(f"Original{original_values.get(value)} (Type: {type(original_values.get(value))}), Current: {values[value]} (Type: {type(values[value])})")



    summary_layout = [
                [
                    sg.Table(
                        summary,
                        headings=["field", "value"],
                        auto_size_columns=False,
                        justification="left",
                        col_widths=[20, 50],
                        display_row_numbers=False,  # Optional: Do not display row numbers
                        key="-TABLE-",
                        expand_y=True
                    )
                ],
                [
                    sg.Button("Edit", key="edit_button"),
                    sg.Button("OK", key="ok_button"),
                ]
    ]

    window = sg.Window(
        "Summary",
        summary_layout,
        location=(300, 0),
        size=(850, 1000),
        finalize=True  # finalize the window
        )

    # Perform an initial window.read() to populate the Table (Treeview) widget
    event, values = window.read(timeout=10)

    table = window["-TABLE-"]
    treeview = table.Widget

    # Create a custom color tag
    treeview.tag_configure("yellow", background="dark blue")

    # Find out the IDs of the items in the treeview
    item_ids = treeview.get_children()

    # Apply that tag to the rows that need to be highlighted
    for i, item_id in enumerate(item_ids):
        if summary[i][2] == 'yellow':
            treeview.item(item_id, tags=("yellow",))

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "ok_button" or event == "edit_button":
            break
    window.close()
    return event


def test_family_compound(values, window, family_compound_values):
    family_compounds = values["family_compound"].split()
    error_string = ""
    for family_compound in family_compounds:
        if family_compound not in family_compound_values:
            error_string += f"{family_compound} "

    if error_string:
        window["family_compound_error"].update(
            error_string, text_color="red")
        window["family_compound"].update(text_color="red")
    else:
        window["family_compound_error"].update("")
        window["family_compound"].update(text_color="darkgray")


def test_family_idioms(values, window, family_idiom_values):
    family_idioms = values["family_idioms"].split()
    error_string = ""
    for idiom_part in family_idioms:
        if idiom_part not in family_idiom_values:
            error_string += f"{idiom_part} "

    if error_string:
        window["family_idioms_error"].update(
            error_string, text_color="red")
        window["family_idioms"].update(text_color="red")
    else:
        window["family_idioms_error"].update("")
        window["family_idioms"].update(text_color="darkgray")


def remove_word_to_add(values, window, words_to_add_list):
    try:
        words_to_add_list = [
            word for word in words_to_add_list
            if word not in values["word_to_add"]
        ]
        window["word_to_add"].update(words_to_add_list)
    except UnboundLocalError as e:
        window["messages"].update(e, text_color="red")

    return words_to_add_list


def add_to_word_to_add(words_to_add_list, word_to_add, window):
    """Update word_to_add_list with a new word,
    wither from construction or control_a."""
    words_to_add_list.insert(0, word_to_add)
    window["add_construction"].update("")
    window["messages"].update(
        f"{word_to_add} added to words to add list",
        text_color="white")

    return words_to_add_list


def save_gui_state(pth, values, words_to_add_list):
    save_state: tuple = (values, words_to_add_list)
    print(f"[green]saving gui state, values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")

    # Check if the file exists and create a backup if it does
    if os.path.exists(pth.save_state_path):
        backup_path = str(pth.save_state_path) + '_backup'
        shutil.copy2(pth.save_state_path, backup_path)
        print(f"[yellow]Backed up old state to {backup_path}")
    
    # Save the new state
    with open(pth.save_state_path, "wb") as f:
        pickle.dump(save_state, f)


def load_gui_state(pth):
    with open(pth.save_state_path, "rb") as f:
        save_state = pickle.load(f)
    values = save_state[0]
    words_to_add_list = save_state[1]
    print(f"[green]loading gui state, values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")
    return values, words_to_add_list


def test_construction(values, window, lemma_clean_list):
    construction_list = values["construction"].split(" + ")
    error_string = ""
    for c in construction_list:
        if c not in lemma_clean_list:
            error_string += f"{c} "
    window["construction_error"].update(error_string, text_color="red")


def replace_sandhi(
        text: str, field: str, 
        sandhi_dict: dict, hyphenations_dict: dict, window
    ) -> None:
    """Replace Sandhi and hypenated words."""
    
    pali_alphabet_string = "".join(pali_alphabet)
    splits = re.split(f"([^{pali_alphabet_string}])", text)

    for i in range(len(splits)):
        word = splits[i]
        if word in sandhi_dict:
            splits[i] = "//".join(sandhi_dict[word]["contractions"])

        if word in hyphenations_dict:
            splits[i] = hyphenations_dict[word]
    
    text = "".join(splits)

    # fix bold 'ti
    text = text.replace("</b>ti", "</b>'ti")
    # fix bold 'ti
    text = text.replace("</b>nti", "n</b>'ti")
    # fix bold comma
    text = text.replace(",</b>", "</b>,")
    # fix bold stop
    text = text.replace(".</b>", "</b>.")
    # fix bold quote
    text = text.replace("'</b>'", "</b>'")
    # fix 'tipi
    text = text.replace("'tipi", "'ti'pi")
    # remove [...]
    text = re.sub(r"\[[^]]*\]", "", text)
    # remove double spaces
    text = re.sub(" +", " ", text)
    # remove digits in front
    text = re.sub(r"^\d*\. ", "", text)
    # remove space comma
    text = text.replace(" ,", ",")
    # remove space fullstop
    text = text.replace(" .", ".")
    # remove spaces front n back
    text = text.strip()

    window[field].update(text)


def test_username(sg):
    """If no username in config.ini, save one.
    Return user_1 or user_2."""
    while True:
        if not config_test_option("user", "username"):
            username = sg.popup_get_text(
                "What is your name?", title="username", location=(400, 400))
            if username:
                config_update("user", "username", username)
                break
        else:
            break
    if config_test("user", "username", "1"):
        username = "primary_user"
    else:
        username = config_read("user", "username")

    return username


def compare_differences(
        book_to_add, pth, values: dict, sg, pali_word_original: Optional[DpdHeadwords], action):
    """Comapre the differences between original and new word.
    Save to corrections or additions TSV."""

    if (
        action == "updated" and
        pali_word_original
    ):
        # check what's changed
        got_comment = set()
        fields = pali_word_original.__dict__
        for field in fields.keys():
            if field in values:
                if str(getattr(pali_word_original, field)) != values[field]:
                    group = None
                    if field in ["source_1", "sutta_1", "example_1"]:
                        group = "source_sutta_example1"
                    elif field in ["source_2", "sutta_2", "example_2"]:
                        group = "source_sutta_example2"
                    elif field in ["derivative", "suffix"]:
                        group = "derivative_suffix"
                    elif field in ["compound_type", "compound_construction"]:
                        group = "compound_type_construction"
                    elif field in ["stem", "pattern"]:
                        group = "stem_pattern"

                    if group not in got_comment:
                        while True:
                            prompt = f"{field} has changed, why?\n"
                            prompt += f"old: {getattr(pali_word_original, field)}\n"
                            prompt += f"new: {values[field]}"
                            comment = sg.popup_get_text(
                                prompt, title="comment", default_text='missing', location=(400, 400))
                            if comment:
                                break

                        if group:
                            got_comment.add(group)

                        if group == "source_sutta_example1":
                            correction = [
                                values["id"],
                                "source_1",
                                values["source_1"],
                                "sutta_1",
                                values["sutta_1"],
                                "example_1",
                                values["example_1"],
                                comment,
                                "", ""]

                        elif group == "source_sutta_example2":
                            correction = [
                                values["id"],
                                "source_2",
                                values["source_2"],
                                "sutta_2",
                                values["sutta_2"],
                                "example_2",
                                values["example_2"],
                                comment,
                                "", ""]

                        elif group == "derivative_suffix":
                            correction = [
                                values["id"],
                                "derivative",
                                values["derivative"],
                                "suffix",
                                values["suffix"],
                                "",
                                "",
                                comment,
                                "", ""]

                        elif group == "compound_type_construction":
                            correction = [
                                values["id"],
                                "compound_type",
                                values["compound_type"],
                                "compound_construction",
                                values["compound_construction"],
                                "",
                                "",
                                comment,
                                "", ""]

                        elif group == "stem_pattern":
                            correction = [
                                values["id"],
                                "stem",
                                values["stem"],
                                "pattern",
                                values["pattern"],
                                "",
                                "",
                                comment,
                                "", ""]

                        else:
                            correction = [
                                values["id"],
                                field,
                                values[field],
                                "",
                                "",
                                "",
                                "",
                                comment,
                                "", ""]

                        with open(pth.corrections_tsv_path, "a") as file:
                            writer = csv.writer(file, delimiter="\t")
                            writer.writerow(correction)

    elif (
        action == "added" or
        not pali_word_original
    ):
        while True:
            prompt = "Please comment on this new word."
            comment = sg.popup_get_text(
                prompt, default_text=f'{book_to_add}', title="comment", location=(400, 400))
            if comment:
                break

        pali_word = values_to_pali_word(values)
        if pth.additions_pickle_path.exists():
            additions_list = Addition.load_additions()
        else:
            additions_list = []
        addition = Addition(pali_word, comment)

        additions_list.append(addition)
        Addition.save_additions(additions_list)


def additions_load(pth) -> List[Tuple]:
    """Load the list of word to add to db from pickle file."""
    with open(pth.additions_pickle_path, "rb") as file:
        additions = pickle.load(file)
        print(additions)
        return additions


def additions_save(pth, additions):
    """Save the list of word to add to db to pickle file."""
    with open(pth.additions_pickle_path, "wb") as file:
        pickle.dump(additions, file)


def load_gui_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    
    gui_config = {
        "theme": config["gui"]["theme"],
        "screen_fraction_width": float(config["gui"]["screen_fraction_width"]),
        "screen_fraction_height": float(config["gui"]["screen_fraction_height"]),
        "window_location": (int(config["gui"]["window_x"]), int(config["gui"]["window_y"])),
        "font": (config["gui"]["font_name"], int(config["gui"]["font_size"])),
        "input_text_color": config["gui"]["input_text_color"],
        "text_color": config["gui"]["text_color"],
        "element_padding": (int(config["gui"]["element_padding_x"]), int(config["gui"]["element_padding_y"])),
        "margins": (int(config["gui"]["margin_x"]), int(config["gui"]["margin_y"]))
    }
    return gui_config


def stasher(pth, values: dict, window):
    with open(pth.stash_path, "wb") as f:
        pickle.dump(values, f)
    window["messages"].update(
        value=f"{values['lemma_1']} stashed", text_color="white")


def unstasher(pth, window):
    exceptions = ["word_to_add"]
    with open(pth.stash_path, "rb") as f:
        unstash = pickle.load(f)
        for key, value in unstash.items():
            if key not in exceptions:
                window[key].update(value)
    window["messages"].update(
        value="unstashed", text_color="white")


def increment_lemma_1(values: dict) -> Tuple[str, str]:
    lemma_1: str = values["lemma_1"]
    pattern: str = r"\d$"
    matches: list = re.findall(pattern, lemma_1)
    last_digit = int(matches[-1]) if matches else None
    if last_digit is not None:
        new_last_digit = last_digit + 1
        updated_lemma_1: str = re.sub(pattern, str(new_last_digit), lemma_1, count=1)
        return (lemma_1, updated_lemma_1)
    else:
        return (f"{lemma_1} 1", f"{lemma_1} 2")


def make_lemma_clean(values) -> str:
    return re.sub(r" \d*$", "", values["lemma_1"])


def make_construction(values) -> str:
    """Make a construction out of root family"""
    lemma_clean = make_lemma_clean(values)

    # root
    if values["root_key"]:
        family = values["family_root"].replace(" ", " + ")
        neg = ""
        if values["neg"]:
            neg = "na + "
        if values["root_base"]:
            # remove (end brackets)
            base = re.sub(r" \(.+\)$", "", values["root_base"])
            # remove front
            base = re.sub("^.+> ", "", base)
            family = re.sub("√.+", base, family)
        return f"{neg}{family} + "

    # compound
    elif re.findall(r"\bcomp\b", values["grammar"]):
        return lemma_clean
    else:
        return lemma_clean


def make_construction_line1(values) -> str:
    # remove line 2
    construction = re.sub(r"\n.+", "", values["construction"])
    # remove phonetic changes >
    construction = re.sub(r">.[^+]+", "", construction)
    return construction


def make_compound_construction(values):
    lemma_clean = make_lemma_clean(values)
    construction_line1 = make_construction_line1(values)
    
    # roots starting with su dur na
    if values["root_key"]:
        if values["construction"].startswith("su "):
            return f"su + {lemma_clean[2:]}"
        elif values["construction"].startswith("dur "):
            return f"dur + {lemma_clean[3:]}"
        elif values["construction"].startswith("na "):
            if lemma_clean.startswith("an"):
                return f"na + {lemma_clean[2:]}"
            elif lemma_clean.startswith("a"):
                return f"na + {lemma_clean[1:]}"
            elif lemma_clean.startswith("na"):
                return f"na + {lemma_clean[2:]}"  
    
    # compounds
    elif re.findall(r"\bcomp\b", values["grammar"]):
        return construction_line1
    
    # dvanda '+' > 'ca'
    elif values["compound_type"] == "dvanda":
        return construction_line1.replace("+", "<b>ca</b>") + " <b>ca</b>"

    # neg kammadhārayas
    elif (
        values["compound_type"] == "kammadhāraya"
        and "neg" in values["neg"] 
    ):
        if lemma_clean.startswith("na"):
            
            # check if there's a double consonant
            if lemma_clean[2] == lemma_clean[3]:
                return f"na + {lemma_clean[3:]}"
            else:
                return f"na + {lemma_clean[2:]}"
            
        elif lemma_clean.startswith("an"):
            return f"na + {lemma_clean[2:]}"
        
        elif lemma_clean.startswith("a"):
            
            # check if there's a double consonant
            if lemma_clean[1] == lemma_clean[2]:
                return f"na + {lemma_clean[2:]}"
            else:
                return f"na + {lemma_clean[1:]}"
        
        elif lemma_clean.startswith("nā"):
            return f"na + a{lemma_clean[2:]}"

    else:
        return lemma_clean


def make_has_values_list(values: dict) -> list[str]:
    """Return a list of all the fields with values."""
    has_value_list = []
    for key, value in values.items():
        if value:
            has_value_list.append(key)
    return has_value_list
