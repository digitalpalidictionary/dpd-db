"""Functions related to the GUI (DPS)."""

import csv
import subprocess
import textwrap

from spellchecker import SpellChecker
from nltk import word_tokenize
from googletrans import Translator
import openai

from db.db_helpers import get_column_names
from db.models import Russian, SBS
from db.get_db_session import get_db_session


from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH
from tools.meaning_construction import make_meaning
from tools.tsv_read_write import read_tsv_dot_dict
from dps.tools.config import OPENAI_API_KEY

db_session = get_db_session(PTH.dpd_db_path)

openai.api_key = OPENAI_API_KEY


class Flags_dps:
    def __init__(self):
        self.sbs_example_1 = True
        self.sbs_example_2 = False
        self.sbs_example_3 = False
        self.sbs_example_4 = False


def dps_reset_flags(flags):
    flags.sbs_example_1 = True
    flags.sbs_example_2 = False
    flags.sbs_example_3 = False
    flags.sbs_example_4 = False


def populate_dps_tab(values, window, dpd_word, ru_word, sbs_word):
    """Populate DPS tab with DPD info."""
    window["dps_dpd_id"].update(dpd_word.id)
    window["dps_pali_1"].update(dpd_word.pali_1)

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

    # synonym
    dps_synonym = ""
    if dpd_word.synonym:
        dps_synonym = dpd_word.synonym
    window["dps_synonym"].update(dps_synonym)

    # antonym
    dps_antonym = ""
    if dpd_word.antonym:
        dps_antonym = dpd_word.antonym
    window["dps_antonym"].update(dps_antonym)

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

    # mp3
    audio = f"audio=[sound:{dpd_word.pali_clean}.mp3]"
    window["dps_sbs_audio"].update(audio)


def load_sbs_index() -> dict:
    file_path = DPSPTH.sbs_index_path
    sbs_index = read_tsv_dot_dict(file_path)
    return sbs_index


def fetch_sbs_index(pali_chant):
    for i in sbs_index:
        if i.pali_chant == pali_chant:
            return i.english_chant, i.chapter


def update_sbs_chant(number, chant, window):
    english, chapter = fetch_sbs_index(chant)
    window[f"dps_sbs_chant_eng_{number}"].update(english)
    window[f"dps_sbs_chapter_{number}"].update(chapter)


def clear_dps(values, window):
    """Clear all value from DPS tab."""
    for value in values:
        if value.startswith("dps_"):
            window[value].update("")


sbs_index = load_sbs_index()


def translate_to_russian_googletrans(meaning, window):
    error_string = ""

    # repace lit. with nothing
    meaning = meaning.replace("lit.", "|")

    # Check if meaning is None or empty
    if not meaning:
        error_string = "No input provided for translation."
        window["dps_google_translate_error"].update(error_string, text_color="red")
        return

    try:
        translator = Translator()
        translation = translator.translate(meaning, dest='ru')
        dps_ru_online_suggestion = translation.text.lower()

        # Add spaces after semicolons and lit. for better readability
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace(";", "; ")
        dps_ru_online_suggestion = dps_ru_online_suggestion.replace("|", "| ")

        window["dps_ru_online_suggestion"].update(dps_ru_online_suggestion, text_color="yellow")
        return dps_ru_online_suggestion

    except Exception as e:
        # Handle any exceptions that occur
        error_string = f"Error during translation of '{meaning}': {e}"
        window["dps_google_translate_error"].update(error_string, text_color="red")
        return error_string  # Placeholder error message


# Helper function to replace abbreviations
def replace_abbreviations(grammar_string, abbreviations_path):
    # Clean the grammar string: Take portion before the first ','
    cleaned_grammar_string = grammar_string.split(',')[0].strip()

    replacements = {}

    # Read abbreviations and their full forms into a dictionary
    with open(abbreviations_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = row[0], row[1]  # select only the first two columns
            replacements[abbrev] = full_form

    # Split the cleaned grammar string by spaces to get individual abbreviations
    abbreviations = cleaned_grammar_string.split()

    # Replace abbreviations in the list
    for idx, abbrev in enumerate(abbreviations):
        if abbrev in replacements:
            abbreviations[idx] = replacements[abbrev]

    # Join the list back into a string
    replaced_string = ' '.join(abbreviations)

    return replaced_string



def translate_with_openai(meaning, pali_1, grammar, window):

    # keep original grammar
    grammar_orig = grammar

    # Replace abbreviations in grammar
    grammar = replace_abbreviations(grammar, PTH.abbreviations_tsv_path)

    # Write pali_1 and grammar to CSV for checking
    with open(DPSPTH.temp_csv_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow([pali_1, grammar_orig, grammar])
    
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
        dps_ru_online_suggestion = response.choices[0].message['content'].replace('**Русский перевод**: ', '').strip().lower()

        window["dps_ru_online_suggestion"].update(dps_ru_online_suggestion)

        # Save to CSV
        with open(DPSPTH.ai_suggestion_history_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([pali_1, meaning, dps_ru_online_suggestion])

        return dps_ru_online_suggestion

    except Exception as e:
        # Handle any exceptions that occur
        error_string = f"Error during translation: {e} - {messages}"
        window["dps_openai_translate_error"].update(error_string, text_color="red")
        return error_string


def copy_and_split_content(sugestion_key, meaning_key, lit_meaning_key, window, values):
    # Get the content to be split and copied
    content = values[sugestion_key]
    
    # Check for the content type and join if it's a list (for multiline)
    if isinstance(content, list):
        content = "\n".join(content)
    
    # Split content based on 'досл.' or 'букв.'
    for delimiter in ['досл.', 'букв.', '|', 'буквально,', 'дословно,', 'лит.']:
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


def display_dps_summary(values, window, sg):

    dps_values_list = [
    "dps_pali_1", "dps_grammar", "dps_meaning", "dps_ru_meaning", "dps_ru_meaning_lit", "dps_sbs_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym", "dps_antonym", "dps_notes", "dps_ru_notes", "dps_sbs_notes", "dps_sbs_source_1", "dps_sbs_sutta_1", "dps_sbs_example_1", "dps_sbs_chant_pali_1", "dps_sbs_chant_eng_1", "dps_sbs_chapter_1", "dps_sbs_source_2", "dps_sbs_sutta_2", "dps_sbs_example_2", "dps_sbs_chant_pali_2", "dps_sbs_chant_eng_2", "dps_sbs_chapter_2", "dps_sbs_source_3", "dps_sbs_sutta_3", "dps_sbs_example_3", "dps_sbs_chant_pali_3", "dps_sbs_chant_eng_3", "dps_sbs_chapter_3", "dps_sbs_source_4", "dps_sbs_sutta_4", "dps_sbs_example_4", "dps_sbs_chant_pali_4", "dps_sbs_chant_eng_4", "dps_sbs_chapter_4", "dps_sbs_class_anki", "dps_sbs_audio", "dps_sbs_category", "dps_sbs_index"]

    summary = []
    for value in values:
        if value in dps_values_list:
            if values[value] != "":
                if len(values[value]) < 40:
                    summary += [[
                        value, values[value]
                    ]]
                else:
                    wrapped_lines = textwrap.wrap(values[value], width=40)
                    summary += [[value, wrapped_lines[0]]]
                    for wrapped_line in wrapped_lines:
                        if wrapped_line != wrapped_lines[0]:
                            summary += [["", wrapped_line]]

    summary_layout = [
                [
                    sg.Table(
                        summary,
                        headings=["field", "value"],
                        auto_size_columns=False,
                        justification="left",
                        col_widths=[20, 50],
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

    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == "dps_ok_button" or event == "dps_edit_button":
            break
    window.close()
    return event

ru_spell = SpellChecker(language='ru')
ru_spell.word_frequency.load_text_file(str(DPSPTH.ru_user_dict_path))

def ru_check_spelling(field, error_field, values, window):

    ru_sentence = values[field]
    ru_words = word_tokenize(ru_sentence) 

    ru_misspelled = ru_spell.unknown(ru_words)

    ru_candidates = ""
    for word in ru_misspelled:
        ru_candidates = ru_spell.candidates(word)

    window[error_field].update(f"{ru_candidates}")


def ru_add_spelling(word):
    with open(DPSPTH.ru_user_dict_path, "a", encoding='utf-8') as f:
        f.write(f"{word}\n")


def ru_edit_spelling():
    subprocess.Popen(
        ["code", DPSPTH.ru_user_dict_path])


# dps functions_db

def fetch_ru(id: int) -> Russian:
    """Fetch Russian word from db."""
    return db_session.query(Russian).filter(
        Russian.id == id).first()


def fetch_sbs(id: int) -> SBS:
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
