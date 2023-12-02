"""Functions related to the GUI (DPS)."""

import csv
import subprocess
import textwrap
import requests
import re
import configparser
import openai
import os
import json

from spellchecker import SpellChecker
from nltk import word_tokenize
from googletrans import Translator

from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

from db.db_helpers import get_column_names
from db.models import Russian, SBS, PaliWord, DerivedData
from db.get_db_session import get_db_session


from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths as DPSPTH
from tools.meaning_construction import make_meaning
from tools.tsv_read_write import read_tsv_dot_dict

from tools.cst_sc_text_sets import make_cst_text_set
from tools.cst_sc_text_sets import make_cst_text_set_sutta
from tools.cst_sc_text_sets import make_cst_text_set_from_file
from tools.cst_sc_text_sets import make_sc_text_set

from functions import make_sp_mistakes_list
from functions import make_sandhi_ok_list
from functions import make_variant_list

from rich import print
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from typing import Optional
from tools.pali_sort_key import pali_sort_key

PTH = ProjectPaths()
db_session = get_db_session(PTH.dpd_db_path)

# flags

class Flags_dps:
    def __init__(self):
        self.synoyms = True
        self.sbs_example_1 = True
        self.sbs_example_2 = False
        self.sbs_example_3 = False
        self.sbs_example_4 = False
        self.tested = False
        self.test_next = False
        self.show_fields = True


def dps_reset_flags(flags_dps):
    flags_dps.synoyms = True
    flags_dps.sbs_example_1 = True
    flags_dps.sbs_example_2 = False
    flags_dps.sbs_example_3 = False
    flags_dps.sbs_example_4 = False
    flags_dps.tested = False
    flags_dps.test_next = False
    flags_dps.show_fields = True


# tab maintenance


def populate_dps_tab(values, window, dpd_word, ru_word, sbs_word):
    """Populate DPS tab with DPD info."""
    window["dps_dpd_id"].update(dpd_word.id)
    window["dps_pali_1"].update(dpd_word.pali_1)
    window["dps_id_or_pali_1"].update(dpd_word.pali_1)

    # copy dpd values for tests

    dps_pos = dpd_word.pos
    window["dps_pos"].update(dps_pos)
    dps_family_set = dpd_word.family_set
    window["dps_family_set"].update(dps_family_set)
    dps_suffix = dpd_word.suffix
    window["dps_suffix"].update(dps_suffix)
    dps_verb = dpd_word.verb
    window["dps_verb"].update(dps_verb)
    dps_meaning_lit = dpd_word.meaning_lit
    window["dps_meaning_lit"].update(dps_meaning_lit)
    dps_meaning_1 = dpd_word.meaning_1
    window["dps_meaning_1"].update(dps_meaning_1)


    # grammar
    dps_grammar = dpd_word.grammar
    if dpd_word.neg:
        dps_grammar += f", {dpd_word.neg}"
    if dpd_word.verb:
        dps_grammar += f", {dpd_word.verb}"
    if dpd_word.trans:
        dps_grammar += f", {dpd_word.trans}"
    if dpd_word.plus_case:
        dps_grammar += f" ({dpd_word.plus_case})"
    window["dps_grammar"].update(dps_grammar)

    # meaning
    meaning = make_meaning(dpd_word)
    if dpd_word.meaning_1:
        window["dps_meaning"].update(meaning)
    else:
        meaning = f"(meaing_2) {meaning}"
        window["dps_meaning"].update(meaning)

    # russian
    ru_columns = get_column_names(Russian)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in ru_columns:
                window[value].update(getattr(ru_word, value_clean, ""))

    # sbs
    sbs_columns = get_column_names(SBS)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in sbs_columns:
                window[value].update(getattr(sbs_word, value_clean, ""))

    # root
    root = ""
    if dpd_word.root_key:
        root = f"{dpd_word.root_key} "
        root += f"{dpd_word.rt.root_has_verb} "
        root += f"{dpd_word.rt.root_group} "
        root += f"{dpd_word.root_sign} "
        root += f"({dpd_word.rt.root_meaning})"
    window["dps_root"].update(root)

    # base_or_comp
    base_or_comp = ""
    if dpd_word.root_base:
        base_or_comp += dpd_word.root_base
    elif dpd_word.compound_type:
        base_or_comp += dpd_word.compound_type
    window["dps_base_or_comp"].update(base_or_comp)

    # dps_constr_or_comp_constr
    constr_or_comp_constr = ""
    if dpd_word.compound_construction:
        constr_or_comp_constr += dpd_word.compound_construction
    elif dpd_word.construction:
        constr_or_comp_constr += dpd_word.construction
    window["dps_constr_or_comp_constr"].update(constr_or_comp_constr)

    # synonym_antonym
    dps_syn_ant = ""
    if dpd_word.synonym:
        dps_syn_ant = f"(syn) {dpd_word.synonym}"
    if dpd_word.antonym:
        dps_syn_ant += f"(ant): {dpd_word.antonym}" 
    window["dps_synonym_antonym"].update(dps_syn_ant)

    # notes
    dps_notes = ""
    if dpd_word.notes:
        dps_notes = dpd_word.notes
    window["dps_notes"].update(dps_notes)

    # source_1
    dps_source_1 = ""
    if dpd_word.source_1:
        dps_source_1 = dpd_word.source_1
    window["dps_source_1"].update(dps_source_1)

    # sutta_1
    dps_sutta_1 = ""
    if dpd_word.sutta_1:
        dps_sutta_1 = dpd_word.sutta_1
    window["dps_sutta_1"].update(dps_sutta_1)

    # example_1
    dps_example_1 = ""
    if dpd_word.example_1:
        dps_example_1 = dpd_word.example_1
    window["dps_example_1"].update(dps_example_1)


    # source_2
    dps_source_2 = ""
    if dpd_word.source_2:
        dps_source_2 = dpd_word.source_2
    window["dps_source_2"].update(dps_source_2)

    # sutta_2
    dps_sutta_2 = ""
    if dpd_word.sutta_2:
        dps_sutta_2 = dpd_word.sutta_2
    window["dps_sutta_2"].update(dps_sutta_2)

    # example_2
    dps_example_2 = ""
    if dpd_word.example_2:
        dps_example_2 = dpd_word.example_2
    window["dps_example_2"].update(dps_example_2)

    # dps_sbs_chant_pali
    if values["dps_sbs_chant_pali_1"]:
        chant = values["dps_sbs_chant_pali_1"]
        update_sbs_chant(1, chant, "", window)

    if values["dps_sbs_chant_pali_2"]:
        chant = values["dps_sbs_chant_pali_2"]
        update_sbs_chant(2, chant, "", window)

    if values["dps_sbs_chant_pali_3"]:
        chant = values["dps_sbs_chant_pali_3"]
        update_sbs_chant(3, chant, "", window)

    if values["dps_sbs_chant_pali_4"]:
        chant = values["dps_sbs_chant_pali_4"]
        update_sbs_chant(4, chant, "", window)


def dps_get_original_values(values, dpd_word, ru_word, sbs_word):

    original_values = {}

    original_values["pali_1"] = dpd_word.pali_1

    # For Russian columns
    ru_columns = get_column_names(Russian)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in ru_columns:
                original_values[value_clean] = getattr(ru_word, value_clean, "")

    # For SBS columns
    sbs_columns = get_column_names(SBS)
    for value in values:
        if value.startswith("dps_"):
            value_clean = value.replace("dps_", "")
            if value_clean in sbs_columns:
                original_values[value_clean] = getattr(sbs_word, value_clean, "")
    
    return original_values


def clear_dps(values, window):
    """Clear all value from DPS tab."""
    for value in values:
        if value.startswith("dps_"):
            window[value].update("")


def edit_corrections():
    subprocess.Popen(
        ["libreoffice", PTH.corrections_tsv_path])


def display_dps_summary(values, window, sg, original_values):

    dps_values_list = [
    "dps_pali_1", "dps_grammar", "dps_meaning", "dps_ru_meaning", "dps_ru_meaning_lit", "dps_sbs_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym_antonym", "dps_notes", "dps_ru_notes", "dps_sbs_notes", "dps_sbs_source_1", "dps_sbs_sutta_1", "dps_sbs_example_1", "dps_sbs_chant_pali_1", "dps_sbs_chant_eng_1", "dps_sbs_chapter_1", "dps_sbs_source_2", "dps_sbs_sutta_2", "dps_sbs_example_2", "dps_sbs_chant_pali_2", "dps_sbs_chant_eng_2", "dps_sbs_chapter_2", "dps_sbs_source_3", "dps_sbs_sutta_3", "dps_sbs_example_3", "dps_sbs_chant_pali_3", "dps_sbs_chant_eng_3", "dps_sbs_chapter_3", "dps_sbs_source_4", "dps_sbs_sutta_4", "dps_sbs_example_4", "dps_sbs_chant_pali_4", "dps_sbs_chant_eng_4", "dps_sbs_chapter_4", "dps_sbs_class_anki", "dps_sbs_category"]

    summary = []
    excluded_fields = ["dps_grammar", "dps_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym_antonym", "dps_notes"]

    for value in values:
        if value in dps_values_list:
            if values[value] and value not in excluded_fields:
                # Check if the value is changed
                color = 'yellow' if str(original_values.get(value.replace("dps_", ""))) != str(values[value]) else 'white'

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

    summary_layout = [
                [
                    sg.Table(
                        summary,
                        headings=["field", "value"],
                        auto_size_columns=False,
                        justification="left",
                        col_widths=[20, 50],
                        display_row_numbers=False,  # Optional
                        key="-DPSTABLE-",
                        expand_y=True
                    )
                ],
                [
                    sg.Button("Edit", key="dps_edit_button"),
                    sg.Button("OK", key="dps_ok_button"),
                ]
    ]

    window = sg.Window(
        "Summary",
        summary_layout,
        location=(300, 0),
        size=(1200, 1000)
        )

    event, values = window.read(timeout=100)  # read the window for a short time

    table = window["-DPSTABLE-"]
    treeview = table.Widget
    treeview.tag_configure("yellow", background="dark blue")
    item_ids = treeview.get_children()
    for i, item_id in enumerate(item_ids):
        if summary[i][2] == 'yellow':
            treeview.item(item_id, tags=("yellow",))

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "dps_ok_button" or event == "dps_edit_button":
            break
    window.close()
    return event



# examples related


def load_sbs_index() -> list:
    file_path = DPSPTH.sbs_index_path
    sbs_index = read_tsv_dot_dict(file_path)
    return sbs_index


def fetch_sbs_index(pali_chant):
    sbs_index = load_sbs_index()
    for i in sbs_index:
        if i.pali_chant == pali_chant:
            return i.english_chant, i.chapter
    return None  # explicitly returning None when no match is found


def update_sbs_chant(number, chant, error_field, window):
    result = fetch_sbs_index(chant)
    if result is not None:
        english, chapter = result
        window[f"dps_sbs_chant_eng_{number}"].update(english)
        window[f"dps_sbs_chapter_{number}"].update(chapter)
    else:
        # handle the case when the chant is not found
        error_message = "chant is not found"
        window[error_field].update(error_message)
        window[f"dps_sbs_chant_eng_{number}"].update("")
        window[f"dps_sbs_chapter_{number}"].update("")



def swap_sbs_examples(num1, num2, window, values):
    # Common parts of the keys
    key_parts = ['source', 'sutta', 'example', 'chant_pali', 'chant_eng', 'chapter']

    # Generate the full keys for both numbers
    keys_num1 = [f"dps_sbs_{part}_{num1}" for part in key_parts]
    keys_num2 = [f"dps_sbs_{part}_{num2}" for part in key_parts]

    # Swap values between the two sets of keys
    for key1, key2 in zip(keys_num1, keys_num2):
        # Get values
        value1 = values[key1]
        value2 = values[key2]

        # Update the GUI with swapped values
        window[key1].update(value2)
        window[key2].update(value1)

    # Return swapped values if needed
    return [values[key] for key in keys_num1], [values[key] for key in keys_num2]


def remove_sbs_example(example_num, window):

    fields = ['source', 'sutta', 'example', 'chant_pali', 'chant_eng', 'chapter']

    # Update the fields in the GUI to be empty.
    for field in fields:
        key = f'dps_sbs_{field}_{example_num}'
        window[key].update('')  # Remove the content of the field in the GUI.


def copy_dpd_examples(num_dpd, num_sbs, window, values):
    # Common parts of the keys
    key_parts = ['source', 'sutta', 'example']

    # Generate the full keys for both numbers
    keys_dpd = [f"dps_{part}_{num_dpd}" for part in key_parts]
    keys_sbs = [f"dps_sbs_{part}_{num_sbs}" for part in key_parts]

    # Copy values from keys_dpd to keys_sbs
    for key_dpd, key_sbs in zip(keys_dpd, keys_sbs):
        # Get value from key_dpd
        value_dpd = values.get(key_dpd, None)
        
        # Copy value from key_dpd into key_sbs in the dictionary
        values[key_sbs] = value_dpd

        # Update the GUI for keys_sbs
        window[key_sbs].update(value_dpd)

    # Return values for keys_sbs
    return [values[key] for key in keys_sbs]


KEYS_TEMPLATE = [
    "dps_sbs_source_{}",
    "dps_sbs_sutta_{}",
    "dps_sbs_example_{}",
    "dps_sbs_chant_pali_{}",
    "dps_sbs_chant_eng_{}",
    "dps_sbs_chapter_{}"
]

def stash_values_from(values, num, window, error_field):
    print("Starting stash_values_from...")

    window[error_field].update("")

    # Extract the specific values we're interested in
    keys_to_stash = [key.format(num) for key in KEYS_TEMPLATE]
    
    # Check for empty 'sbs_example_{}' field
    example_key = "dps_sbs_example_{}".format(num)
    if not values.get(example_key):
        error_string = f"Example {num} is empty"
        window[error_field].update(error_string)
        print("Error: Example is empty.")
        return

    # values_to_stash = {key: values[key] for key in keys_to_stash if key in values}
    values_to_stash = {key_template.format(""): values[key] for key, key_template in zip(keys_to_stash, KEYS_TEMPLATE) if key in values}

    print(f"Values to stash: {values_to_stash}")
    
    try:
        with open(DPSPTH.dps_stash_path, "w") as f:
            json.dump(values_to_stash, f)
        print(f"Stashed values to {DPSPTH.dps_stash_path}.")
    except Exception as e:
        print(f"Error while stashing: {e}")
        window[error_field].update(f"Error while stashing: {e}")


def unstash_values_to(window, num, error_field):
    print("Starting unstash_values_to...")

    window[error_field].update("")
    
    # Check if the stash file exists
    if not os.path.exists(DPSPTH.dps_stash_path):
        window[error_field].update("Stash file not found!")
        print(f"Error: {DPSPTH.dps_stash_path} not found.")
        return

    # Load the stashed values
    try:
        with open(DPSPTH.dps_stash_path, "r") as f:
            unstashed_values = json.load(f)
        print(f"Loaded values from {DPSPTH.dps_stash_path}: {unstashed_values}")
    except Exception as e:
        window[error_field].update(f"Error while unstashing: {e}")
        print(f"Error while unstashing: {e}")
        return

    # Update the window with unstashed values
    for key_template in KEYS_TEMPLATE:
        key_to_fetch = key_template.format("")
        key_to_update = key_template.format(num)
        
        if key_to_fetch in unstashed_values:
            window[key_to_update].update(unstashed_values[key_to_fetch])
            print(f"Updated window[{key_to_update}] with value: {unstashed_values[key_to_fetch]}")
        elif "dps_sbs_example_{}".format(num) not in unstashed_values:
            error_string = f"Example {num} was not stashed"
            window[error_field].update(error_string)
            print(f"Error: Example {num} was not stashed.")
            return


# russian related

@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def translate_to_russian_googletrans(meaning, suggestion, error_field, window):

    window[error_field].update("")

    error_string = ""

    # repace lit. with nothing
    meaning = meaning.replace("lit.", "|")

    # Check if meaning is None or empty
    if not meaning:
        error_string = "No input provided for translation."
        window[error_field].update(error_string, text_color="red")
        return

    try:
        translator = Translator()
        translation = translator.translate(meaning, dest='ru')
        dps_ru_online_suggestion = translation.text.lower()

        # Add spaces after semicolons and lit. for better readability
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace(";", "; ")
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace("|", "| ")

        window[suggestion].update(dps_ru_online_suggestion, text_color="Aqua")
        return dps_ru_online_suggestion

    except TimeoutDecoratorError:
        # Handle any exceptions that occur
        error_string = "Timed out"
        window[error_field].update(error_string)
        return error_string

    except Exception as e:
        # Handle any exceptions that occur
        error_string = f"Error: {e} "
        window[error_field].update(error_string)
        return error_string


def replace_abbreviations(grammar_string, abbreviations_path):
    # Clean the grammar string: Take portion before the first ','
    # cleaned_grammar_string = grammar_string.split(',')[0].strip()

    replacements = {}

    # Read abbreviations and their full forms into a dictionary
    with open(abbreviations_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = row[0], row[1]  # select only the first two columns
            replacements[abbrev] = full_form

    # Remove content within brackets
    grammar_string = re.sub(r'\(.*?\)', '', grammar_string)

    # Use regex to split the string in a way that separates punctuations
    abbreviations = re.findall(r"[\w']+|[.,!?;]", grammar_string)

    # Replace abbreviations in the list
    for idx, abbrev in enumerate(abbreviations):
        if abbrev in replacements:
            abbreviations[idx] = replacements[abbrev]

    # Join the list back into a string
    replaced_string = ' '.join(abbreviations)

    return replaced_string


def load_openia_config(filename="config.ini"):
    config = configparser.ConfigParser()
    config.read(filename)
    
    openia_config = {
        "openia": config["openia"]["key"],
    }
    return openia_config

# Setup OpenAI API key
openia_config = load_openia_config()
openai.api_key = openia_config["openia"]


@timeout(15, timeout_exception=TimeoutDecoratorError)  # Setting a 15-second timeout
def call_openai(messages):
    return openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

def handle_openai_response(messages, suggestion_field, error_field, window):
    error_string = ""

    try:
        # Request translation from OpenAI's GPT chat model
        response = call_openai(messages)
        suggestion = response.choices[0].message['content'].replace('**Русский перевод**: ', '').strip().lower() # type: ignore
        window[suggestion_field].update(suggestion, text_color="Aqua")

        return suggestion

    # Handle any exceptions that occur
    except TimeoutDecoratorError:
        error_string = "Timed out"
        print(error_string)
        window[error_field].update(error_string)
        return error_string

    except Exception as e:
        error_string = f"Error: {e} "
        print(error_string)
        window[error_field].update(error_string)
        return error_string


def ru_translate_with_openai(meaning, pali_1, grammar, suggestion_field, error_field, window):
    window[error_field].update("")

    # keep original grammar
    grammar_orig = grammar

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(grammar, PTH.abbreviations_tsv_path)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English text to Russian considering the context."
        },
        {
            "role": "user",
            "content": f"""
                ---
                **Pali Term**: {pali_1}

                **Grammar Details**: {grammar}

                **English Definition**: {meaning}

                Please provide few distinct Russian translations for the English definition, considering the Pali term and its grammatical context. Each synonym should be separated by `;`. Avoid repeating the same word.
                ---
            """
        }
    ]

    suggestion = handle_openai_response(messages, suggestion_field, error_field, window)

    # Save to CSV
    if suggestion != "Timed out":
        with open(DPSPTH.ai_ru_suggestion_history_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            # Write the required columns to the CSV
            writer.writerow([pali_1, grammar_orig, grammar, meaning, suggestion])

    return suggestion


def ru_notes_translate_with_openai(notes, pali_1, grammar, suggestion_field, error_field, window):
    window[error_field].update("")

    # keep original grammar
    grammar_orig = grammar

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(grammar, PTH.abbreviations_tsv_path)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a sophisticated translation model specialized in translating English notes to Russian, particularly in the context of Pāli terms and their grammatical nuances."        
        },
        {
            "role": "user",
            "content": f"""
                ---
                **Pali Term**: {pali_1}

                **Grammar Details**: {grammar}

                **English Notes**: {notes}

                Translate the English notes into Russian. Make sure to take into account that these notes pertain to the Pāli term mentioned, and consider the provided grammatical context.
                ---
            """
        }
    ]

    suggestion = handle_openai_response(messages, suggestion_field, error_field, window)

    # Save to CSV
    if suggestion != "Timed out":
        with open(DPSPTH.ai_ru_notes_suggestion_history_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            # Write the required columns to the CSV
            writer.writerow([pali_1, grammar_orig, grammar, notes, suggestion])

    return suggestion


def en_translate_with_openai(pali_1, grammar, example, suggestion_field, error_field, window):
    window[error_field].update("")

    # keep original grammar
    grammar_orig = grammar

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(grammar, PTH.abbreviations_tsv_path)
    
    # Generate the chat messages based on provided values
    messages = [
        {
            "role": "system",
            "content": "You are a sophisticated translation model specialized in Pāli to English translations, capable of considering context and grammatical details."
        },
        {
            "role": "user",
            "content": f"""
                ---
                **Pali Term**: {pali_1}

                **Grammar Details**: {grammar}

                **Contextual Pali Sentences**: {example}

                Given the details provided, list distinct English synonyms for the specified Pāli term, separated by `;`. For example: "word1; word2; word3". Ensure no repetition.
                ---
            """
        }
    ]
    
    suggestion = handle_openai_response(messages, suggestion_field, error_field, window)

    # Save to CSV
    if suggestion != "Timed out":
        with open(DPSPTH.ai_en_suggestion_history_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            # Write the required columns to the CSV
            writer.writerow([pali_1, grammar_orig, grammar, example, suggestion])

    return suggestion


def copy_and_split_content(sugestion_key, meaning_key, lit_meaning_key, error_field, window, values):

    window[error_field].update("")

    # Get the content to be split and copied
    content = values[sugestion_key]

    if not content:
        error_string = "field is empty"
        window[error_field].update(error_string)
        return

    # Check for the content type and join if it's a list (for multiline)
    if isinstance(content, list):
        content = "\n".join(content)
    
    # Split content based on 'досл.' or 'букв.'
    for delimiter in ['досл.', 'букв.', '|', 'буквально', 'дословно', 'лит.']:
        if delimiter in content:
            before_delimiter, after_delimiter = content.split(delimiter, 1)

            # Remove trailing spaces and semicolons
            before_delimiter = before_delimiter.rstrip('; ').strip()
            
            # Update the GUI for meaning_key and lit_meaning_key
            window[meaning_key].update(before_delimiter)
            window[lit_meaning_key].update(after_delimiter.strip())
            return
    
    # If none of the delimiters are found, just update the meaning_key field
    window[meaning_key].update(content)


YANDEX_SPELLER_API = "https://speller.yandex.net/services/spellservice.json/checkText"


def ru_check_spelling(field, error_field, values, window):

    window[error_field].update("")
    window[error_field].set_size((50, 1))

    ru_spell = SpellChecker(language='ru')
    ru_spell.word_frequency.load_text_file(str(DPSPTH.ru_user_dict_path))
    
    ru_sentence = values[field]
    ru_words = word_tokenize(ru_sentence) 
    ru_misspelled = ru_spell.unknown(ru_words)

    if ru_misspelled:
        print(f"offline ru_misspelled {ru_misspelled}")

    # Load custom dictionary words
    with open(DPSPTH.ru_user_dict_path, 'r', encoding='utf-8') as f:
        custom_words = set(f.read().splitlines())

    # Filter out words that are in the custom dictionary
    ru_misspelled = [word for word in ru_misspelled if word not in custom_words]

    if ru_misspelled:
        # Confirm with Yandex Speller
        yandex_checked_words = get_spelling_suggestions(' '.join(ru_misspelled), return_original=True)
        
        # Filter out words that are confirmed as correct by Yandex Speller
        truly_misspelled = [word for word in ru_misspelled if word in yandex_checked_words]

        if truly_misspelled:
            print(f"yandex truly_misspelled {truly_misspelled}")  

            # For the truly misspelled words, obtain suggestions from Yandex Speller and the local spellchecker
            suggestions = []
            for word in truly_misspelled:
                suggestions.extend(get_spelling_suggestions(word))

            # If no suggestions were found, display a custom message
            if not suggestions:
                custom_message = "?"
                window[error_field].update(custom_message)
                return

            # Else process and display the suggestions
            # Joining the flattened list
            correction_text = ", ".join(suggestions)

            # Wrap the correction_text and join it into a multiline string
            wrapped_correction = "\n".join(textwrap.wrap(correction_text, width=30))  # Assuming width of 30 characters

            num_lines = len(wrapped_correction.split('\n'))

            window[error_field].set_size((50, num_lines))  # Adjust the size of the Text element based on the number of lines
            window[error_field].update(wrapped_correction)  

        # If Yandex Speller does not recognize them as errors, clear the error field
        else:
            window[error_field].update("")
            return
        
    else:
        window[error_field].set_size((50, 1))  # Reset to default size
        window[error_field].update("")


def get_spelling_suggestions(text, return_original=False):
    suggestions = []
    try:
        response = requests.post(YANDEX_SPELLER_API, data={'text': text}, timeout=10)  # Adding a timeout for the request
        response.raise_for_status()  # This will raise an error if the HTTP request returned an unsuccessful status code
        result = response.json()

        for word in result:
            if return_original:
                suggestions.append(word['word'])
            elif word['s']:  # Ensure there are suggestions
                if isinstance(word['s'], list):  # Check if 's' is a list
                    suggestions.extend(word['s'])  # Add all suggestions for the misspelled word
                else:
                    suggestions.append(word['s'])  # Directly add the string

    except requests.ConnectionError:
        print("Failed to connect to Yandex Speller. Please check your internet connection.")
        suggestions = "No connection"
    except requests.Timeout:
        print("Request to Yandex Speller timed out. Please try again later.")
        suggestions = "Timed out"
    except requests.RequestException as e:  # This will catch any other exception from the `requests` library
        print(f"An error occurred while connecting to Yandex Speller: {e}")
        suggestions = "Some error"

    return suggestions


def ru_add_spelling(word):
    with open(DPSPTH.ru_user_dict_path, "a", encoding='utf-8') as f:
        f.write(f"{word}\n")


def ru_edit_spelling():
    subprocess.Popen(
        ["code", DPSPTH.ru_user_dict_path])


def tail_log():
    subprocess.Popen(["gnome-terminal", "--", "tail", "-n", "+0", "-f", "/home/deva/logs/gui.log"])
    


def dps_make_words_to_add_list(pth: ProjectPaths, __window__, book: str) -> list:
    cst_text_list = make_cst_text_set(pth, [book])
    sc_text_list = make_sc_text_set(pth, [book])
    original_text_list = list(cst_text_list) + list(sc_text_list)

    sp_mistakes_list = make_sp_mistakes_list(PTH)
    variant_list = make_variant_list(PTH)
    sandhi_ok_list = make_sandhi_ok_list(PTH)
    all_inflections_set = dps_make_all_inflections_set()

    text_set = set(cst_text_list) | set(sc_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    text_list = sorted(text_set, key=lambda x: original_text_list.index(x))
    print(f"words_to_add: {len(text_list)}")

    return text_list


def dps_make_words_to_add_list_sutta(pth: ProjectPaths, sutta_name, book: str) -> list:
    cst_text_list = make_cst_text_set_sutta(pth, sutta_name, [book])

    sp_mistakes_list = make_sp_mistakes_list(PTH)
    variant_list = make_variant_list(PTH)
    sandhi_ok_list = make_sandhi_ok_list(PTH)
    all_inflections_set = dps_make_all_inflections_set()

    text_set = set(cst_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    cst_text_index = {text: index for index, text in enumerate(cst_text_list)}
    text_list = sorted(text_set, key=lambda x: cst_text_index.get(x, float('inf')))

    print(f"words_to_add: {len(text_list)}")

    return text_list


def dps_make_words_to_add_list_from_text() -> list:
    cst_text_list = make_cst_text_set_from_file()

    sp_mistakes_list = make_sp_mistakes_list(PTH)
    variant_list = make_variant_list(PTH)
    sandhi_ok_list = make_sandhi_ok_list(PTH)
    all_inflections_set = dps_make_all_inflections_set()

    text_set = set(cst_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    cst_text_index = {text: index for index, text in enumerate(cst_text_list)}
    text_list = sorted(text_set, key=lambda x: cst_text_index.get(x, float('inf')))
    print(f"words_to_add: {len(text_list)}")

    return text_list


def dps_make_words_to_add_list_from_text_filtered(source) -> list:
    cst_text_list = make_cst_text_set_from_file()

    sp_mistakes_list = make_sp_mistakes_list(PTH)
    variant_list = make_variant_list(PTH)
    sandhi_ok_list = make_sandhi_ok_list(PTH)
    all_inflections_set = dps_make_filtered_inflections_set(source)

    text_set = set(cst_text_list)
    text_set = text_set - set(sandhi_ok_list)
    text_set = text_set - set(sp_mistakes_list)
    text_set = text_set - set(variant_list)
    text_set = text_set - all_inflections_set
    cst_text_index = {text: index for index, text in enumerate(cst_text_list)}
    text_list = sorted(text_set, key=lambda x: cst_text_index.get(x, float('inf')))
    print(f"words_to_add: {len(text_list)}")

    return text_list


# functions which make a list of words from id list
def read_ids_from_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        next(tsv_reader)  # Skip header row
        return [int(row[0]) for row in tsv_reader]  # Extracting IDs only from the first column


def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [x for x in ordered_ids if not (x in seen or seen.add(x))]
    return ordered_ids_no_duplicates


def fetch_matching_words_from_db(__WHAT_TO_UPDATE__, __ORIGINAL_HAS_VALUE__) -> list:

    ordered_ids = read_ids_from_tsv(DPSPTH.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    matching_words = []
    for word_id in ordered_ids:
        word = db_session.query(PaliWord).filter(PaliWord.id == word_id).first()
        # if word and word.sbs:
        #     attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)
        #     if ORIGINAL_HAS_VALUE and attr_value:
        #         matching_words.append(word.pali_1)
        #     elif not ORIGINAL_HAS_VALUE and not attr_value:
        #         matching_words.append(word.pali_1)
        if word and not word.sbs:
            matching_words.append(word.pali_1)

    print(f"words_to_add: {len(matching_words)}")
    return matching_words


def update_words_value(WHAT_TO_UPDATE, SOURCE):
    # Fetch the matching words
    ordered_ids = read_ids_from_tsv(DPSPTH.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    print(WHAT_TO_UPDATE)
    print(SOURCE)

    updated_count = 0

    for word_id in ordered_ids:
        word = db_session.query(PaliWord).filter(PaliWord.id == word_id).first()
        if not word or not word.sbs:
            continue

        attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)

        all_examples_present = all([
            getattr(word.sbs, 'sbs_example_1', None),
            getattr(word.sbs, 'sbs_example_2', None),
            getattr(word.sbs, 'sbs_example_3', None),
            getattr(word.sbs, 'sbs_example_4', None)
        ])

        print(f"Checking word ID: {word_id}")
        print(f"all_examples_present: {all_examples_present}")
        print(f"attr_value: {attr_value}")

        if all_examples_present and not attr_value:
            setattr(word.sbs, WHAT_TO_UPDATE, SOURCE)
            updated_count += 1
            print(f"{word.id} - {WHAT_TO_UPDATE} with {SOURCE}", flush=True)

    db_session.close()
    print(f"{updated_count} rows have been updated with {SOURCE}.")


def print_words_value(WHAT_TO_UPDATE, SOURCE):
    # Fetch the matching words
    ordered_ids = read_ids_from_tsv(DPSPTH.id_to_add_path)
    ordered_ids = remove_duplicates(ordered_ids)

    print(WHAT_TO_UPDATE)
    print(SOURCE)

    for word_id in ordered_ids:
        word = db_session.query(PaliWord).filter(PaliWord.id == word_id).first()
        if not word or not word.sbs:
            continue

        attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)

        all_examples_present = all([
            getattr(word.sbs, 'sbs_example_1', None),
            getattr(word.sbs, 'sbs_example_2', None),
            getattr(word.sbs, 'sbs_example_3', None),
            getattr(word.sbs, 'sbs_example_4', None)
        ])
        if all_examples_present and not attr_value:
            setattr(word.sbs, WHAT_TO_UPDATE, SOURCE)
            print(f"{word.id} - {WHAT_TO_UPDATE} with {SOURCE}", flush=True)


def update_sbs_category(pali_1, source):
    db_session = get_db_session(PTH.dpd_db_path)

    word = db_session.query(PaliWord).filter(PaliWord.pali_1 == pali_1).first()

    if word and word.sbs:
        word.sbs.sbs_category = source
        db_session.commit()
    
    db_session.close()


def words_in_db_from_source(source):
    db_session = get_db_session(PTH.dpd_db_path)

    dpd_db = db_session.query(PaliWord).all()

    matching_words = []

    for i in dpd_db:
        if i.sbs is None or not (
            i.sbs.sbs_source_1 == source or
            i.sbs.sbs_source_2 == source or
            i.sbs.sbs_source_3 == source or
            i.sbs.sbs_source_4 == source
        ):
            if i.source_1 == source or i.source_2 == source:
                matching_words.append(i.pali_1)

    print(f"from {source} words_to_add: {len(matching_words)}")

    return matching_words


# db functions


def fetch_ru(id: int) -> Optional[Russian]:
    """Fetch Russian word from db."""
    return db_session.query(Russian).filter(
        Russian.id == id).first()


def fetch_sbs(id: int) -> Optional[SBS]:
    """Fetch SBS word from db."""
    return db_session.query(SBS).filter(
        SBS.id == id).first()


def dps_update_db(
        values, window, dpd_word, ru_word, sbs_word) -> None:
    """Update Russian and SBS tables with DPS edits."""
    merge = None
    if not ru_word:
        merge = True
        ru_word = Russian(id=dpd_word.id)
    if not sbs_word:
        sbs_word = SBS(id=dpd_word.id)

    for value in values:
        if value.startswith("dps_ru"):
            attribute = value.replace("dps_", "")
            new_value = values[value]
            setattr(ru_word, attribute, new_value)
        if value.startswith("dps_sbs"):
            attribute = value.replace("dps_", "")
            new_value = values[value]
            setattr(sbs_word, attribute, new_value)

    if merge:
        db_session.merge(ru_word)
        db_session.merge(sbs_word)
    else:
        db_session.add(ru_word)
        db_session.add(sbs_word)
    db_session.commit()

    window["messages"].update(
    f"'{values['dps_id_or_pali_1']}' updated in db",
    text_color="Lime")


def dps_get_synonyms(pos: str, string_of_meanings: str, window, error_field) -> Optional[str]:

    string_of_meanings = re.sub(r" \(.*?\)|\(.*?\) ", "", string_of_meanings)
    list_of_meanings = string_of_meanings.split("; ")

    results = db_session.query(PaliWord).join(Russian).filter(
            PaliWord.pos == pos,
            or_(*[PaliWord.meaning_1.like(f"%{meaning}%") for meaning in list_of_meanings]),
            Russian.ru_meaning.isnot(None),  # Ensure ru_meaning is not null
            Russian.ru_meaning != ""         # Ensure ru_meaning is not an empty string
        ).options(joinedload(PaliWord.ru)).all()

    meaning_dict = {}
    for i in results:
        if i.meaning_1:  # check if it's not None and not an empty string
            for meaning in i.meaning_1.split("; "):
                meaning_clean = re.sub(r" \(.*?\)|\(.*?\) ", "", meaning)
                if meaning_clean in list_of_meanings:
                    if meaning_clean not in meaning_dict:
                        meaning_dict[meaning_clean] = set([i.pali_clean])
                    else:
                        meaning_dict[meaning_clean].add(i.pali_clean)

    synonyms = set()
    for key_1 in meaning_dict:
        for key_2 in meaning_dict:
            if key_1 != key_2:
                intersection = meaning_dict[key_1].intersection(
                    meaning_dict[key_2])
                synonyms.update(intersection)

    if not synonyms:
        # Update error_field in window with appropriate message
        window[error_field].update("No synonyms found that fit the filter.")
        return None  # or some other value indicating failure


    synonyms = ", ".join(sorted(synonyms, key=pali_sort_key))
    print(synonyms)
    return synonyms


def dps_make_all_inflections_set():
    
    # Joining tables and filtering where Russian.ru_meaning is not empty
    inflections_db = db_session.query(DerivedData) \
                            .join(PaliWord, PaliWord.id == DerivedData.id) \
                            .join(Russian, PaliWord.id == Russian.id) \
                            .filter((Russian.ru_meaning.isnot(None)) & 
                                    (Russian.ru_meaning != '')) \
                            .all()

    dps_all_inflections_set = set()
    for i in inflections_db:
        dps_all_inflections_set.update(i.inflections_list)

    print(f"dps_all_inflections_set: {len(dps_all_inflections_set)}")

    return dps_all_inflections_set


def dps_make_filtered_inflections_set(source):
    
    # Begin the query
    query = db_session.query(DerivedData)
    
    # Join tables
    query = query.join(PaliWord, PaliWord.id == DerivedData.id)
    query = query.join(SBS, PaliWord.id == SBS.id)
    
    # Apply filters if 'source' contains in any of sbs_cource(s)
    query = query.filter(
        or_(
            SBS.sbs_source_1.ilike(f"%{source}%"), 
            SBS.sbs_source_2.ilike(f"%{source}%"), 
            SBS.sbs_source_3.ilike(f"%{source}%"), 
            SBS.sbs_source_4.ilike(f"%{source}%")
        )
    )

    # Execute the query
    inflections_db = query.all()

    dps_filtered_inflections_set = set()
    for i in inflections_db:
        dps_filtered_inflections_set.update(i.inflections_list)

    print(f"dps_filtered_inflections_set: {len(dps_filtered_inflections_set)}")

    return dps_filtered_inflections_set


def get_next_ids_dps(window):
    used_ids = db_session.query(PaliWord.id).order_by(PaliWord.id).all()

    def find_largest_id():
        return max(used_id.id for used_id in used_ids) if used_ids else 0

    largest_id = find_largest_id()

    next_id = largest_id + 10000

    print(next_id)

    window["id"].update(next_id)