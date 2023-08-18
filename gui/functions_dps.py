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


from db.db_helpers import get_column_names
from db.models import Russian, SBS
from db.get_db_session import get_db_session


from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH
from tools.meaning_construction import make_meaning
from tools.tsv_read_write import read_tsv_dot_dict

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


def dps_reset_flags(flags_dps):
    flags_dps.synoyms = True
    flags_dps.sbs_example_1 = True
    flags_dps.sbs_example_2 = False
    flags_dps.sbs_example_3 = False
    flags_dps.sbs_example_4 = False
    flags_dps.tested = False
    flags_dps.test_next = False


# tab maintenance


def populate_dps_tab(values, window, dpd_word, ru_word, sbs_word):
    """Populate DPS tab with DPD info."""
    window["dps_dpd_id"].update(dpd_word.id)
    window["dps_pali_1"].update(dpd_word.pali_1)

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
        update_sbs_chant(1, chant, window)

    if values["dps_sbs_chant_pali_2"]:
        chant = values["dps_sbs_chant_pali_2"]
        update_sbs_chant(2, chant, window)

    if values["dps_sbs_chant_pali_3"]:
        chant = values["dps_sbs_chant_pali_3"]
        update_sbs_chant(3, chant, window)

    if values["dps_sbs_chant_pali_4"]:
        chant = values["dps_sbs_chant_pali_4"]
        update_sbs_chant(4, chant, window)


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
        ["code", PTH.corrections_tsv_path])


def display_dps_summary(values, window, sg, original_values):

    dps_values_list = [
    "dps_pali_1", "dps_grammar", "dps_meaning", "dps_ru_meaning", "dps_ru_meaning_lit", "dps_sbs_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym_antonym", "dps_notes", "dps_ru_notes", "dps_sbs_notes", "dps_sbs_source_1", "dps_sbs_sutta_1", "dps_sbs_example_1", "dps_sbs_chant_pali_1", "dps_sbs_chant_eng_1", "dps_sbs_chapter_1", "dps_sbs_source_2", "dps_sbs_sutta_2", "dps_sbs_example_2", "dps_sbs_chant_pali_2", "dps_sbs_chant_eng_2", "dps_sbs_chapter_2", "dps_sbs_source_3", "dps_sbs_sutta_3", "dps_sbs_example_3", "dps_sbs_chant_pali_3", "dps_sbs_chant_eng_3", "dps_sbs_chapter_3", "dps_sbs_source_4", "dps_sbs_sutta_4", "dps_sbs_example_4", "dps_sbs_chant_pali_4", "dps_sbs_chant_eng_4", "dps_sbs_chapter_4", "dps_sbs_class_anki", "dps_sbs_category"]

    summary = []
    excluded_fields = ["dps_grammar", "dps_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym_antonym", "dps_notes"]

    for value in values:
        if value in dps_values_list:
            if values[value] != "" and value not in excluded_fields:
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


def update_sbs_chant(number, chant, window):
    result = fetch_sbs_index(chant)
    if result is not None:
        english, chapter = result
        window[f"dps_sbs_chant_eng_{number}"].update(english)
        window[f"dps_sbs_chapter_{number}"].update(chapter)
    else:
        # handle the case when the chant is not found
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

        window[suggestion].update(dps_ru_online_suggestion, text_color="yellow")
        return dps_ru_online_suggestion

    except Exception as e:
        # Handle any exceptions that occur
        error_string = f"Error: {e}"
        window[error_field].update(error_string)
        return error_string  # Placeholder error message


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


def translate_with_openai(meaning, pali_1, grammar, suggestion, error_field, window):

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

**English Grammar Details**: {grammar}

**English Definition**: {meaning}

Please provide few distinct Russian translations for the English definition, considering the Pali term and its grammatical context. Each synonym should be separated by `;`. Avoid repeating the same word.
---
            """
        }
    ]
    
    error_string = ""

    
    try:
        # Request translation from OpenAI's GPT chat model
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        dps_ru_online_suggestion = response.choices[0].message['content'].replace('**Русский перевод**: ', '').strip().lower() # type: ignore

        window[suggestion].update(dps_ru_online_suggestion)

        # Save to CSV
        with open(DPSPTH.ai_suggestion_history_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            # Write the required columns to the CSV
            writer.writerow([pali_1, grammar_orig, grammar, meaning, dps_ru_online_suggestion])


        return dps_ru_online_suggestion

    except Exception as e:
        # Handle any exceptions that occur
        error_string = f"error: {e} "
        window[error_field].update(error_string)
        return error_string


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

        # If Yandex Speller does not recognize them as errors, clear the error field
        if not truly_misspelled:
            window[error_field].update("")
            return
        
        # For the truly misspelled words, obtain suggestions from Yandex Speller and the local spellchecker
        suggestions = []
        for word in truly_misspelled:
            suggestions.extend(get_spelling_suggestions(word))

        # If no suggestions were found, display a custom message
        if not suggestions and truly_misspelled:
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
    except requests.Timeout:
        print("Request to Yandex Speller timed out. Please try again later.")
    except requests.RequestException as e:  # This will catch any other exception from the `requests` library
        print(f"An error occurred while connecting to Yandex Speller: {e}")

    return suggestions


def ru_add_spelling(word):
    with open(DPSPTH.ru_user_dict_path, "a", encoding='utf-8') as f:
        f.write(f"{word}\n")


def ru_edit_spelling():
    subprocess.Popen(
        ["code", DPSPTH.ru_user_dict_path])


def tail_log():
    subprocess.Popen(["gnome-terminal", "--", "tail", "-f", "temp/.gui_errors.txt"])
    

def extract_sutta_from_file(sutta_name, book):
    # Read the file content

    print(PTH.cst_txt_dir.joinpath(book))  # Debugging print

    with open(PTH.cst_txt_dir.joinpath(book), "r") as f:
        text = f.read()

    print(f"Loaded file with {len(text)} characters.")  # Debugging print

    # Search for the beginning of the sutta using the sutta_name
    start_index = text.find(sutta_name)
    
    # If sutta_name is not found in the text, return None
    if start_index == -1:
        print(f"'{sutta_name}' not found in the text.")
        return None
    print(f"Start index of sutta: {start_index}")  # Debugging print

    # Adjust end pattern based on the file's name
    if book.startswith(("s01", "s02")):
        end_pattern = f"{sutta_name} niṭṭhitaṃ"
    elif book.startswith(("s03", "s04", "s05")):
        end_pattern = "suttaṃ"
    else:
        print(f"Unknown file name pattern: {book}")
        return None
    
    # Search for the end of the sutta using the end_pattern
    end_index = text.find(end_pattern, start_index + len(sutta_name))

    
    # If the end pattern is not found after the start index, return None
    if end_index == -1:
        print(f"End pattern '{end_pattern}' not found in the text after '{sutta_name}'.")
        return None
    print(f"End index of sutta: {end_index}")  # Debugging print

    # Extract the sutta from the text using the start and end indices
    sutta = text[start_index:end_index + len(end_pattern)]

    return sutta
