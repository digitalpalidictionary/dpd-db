"""Functions related to the GUI (DPS)."""

import csv
import subprocess
import textwrap
import requests
import os
import json
import pickle
import shutil

from rich import print

from requests.exceptions import RequestException
from difflib import SequenceMatcher

from tools.tsv_read_write import read_tsv_dict, write_tsv_dot_dict

from dps.tools.ai_related import load_translaton_examples
from dps.tools.ai_related import replace_abbreviations
from dps.tools.ai_related import handle_openai_response
from dps.tools.ai_related import get_openai_client
from dps.tools.ai_related import generate_messages_for_meaning
from dps.tools.ai_related import generate_messages_for_notes
from dps.tools.ai_related import generate_messages_for_english_meaning

from dps.tools.spell_check import SpellCheck


# flags
class Flags_dps:
    def __init__(self):
        self.synonyms = True
        self.sbs_example_1 = True
        self.sbs_example_2 = False
        self.sbs_example_3 = False
        self.sbs_example_4 = False
        self.tested = False
        self.test_next = False
        self.show_fields = True
        self.next_word = False


def dps_reset_flags(flags_dps):
    flags_dps.synonyms = True
    flags_dps.sbs_example_1 = True
    flags_dps.sbs_example_2 = False
    flags_dps.sbs_example_3 = False
    flags_dps.sbs_example_4 = False
    flags_dps.tested = False
    flags_dps.test_next = False
    flags_dps.show_fields = True
    flags_dps.next_word = False


# tab maintenance


def clear_dps(values, window):
    """Clear all value from DPS tab."""
    for value in values:
        if value.startswith("dps_") and not value.startswith("dps_test_"):
            window[value].update("")


def edit_corrections(pth):
    subprocess.Popen(
        ["libreoffice", pth.corrections_tsv_path])


def display_dps_summary(values, window, sg, original_values):

    dps_values_list = [
    "dps_lemma_1", "dps_grammar", "dps_meaning", "dps_ru_meaning", "dps_ru_meaning_lit", "dps_sbs_meaning", "dps_root", "dps_base_or_comp", "dps_constr_or_comp_constr", "dps_synonym_antonym", "dps_notes", "dps_ru_notes", "dps_sbs_notes", "dps_sbs_source_1", "dps_sbs_sutta_1", "dps_sbs_example_1", "dps_sbs_chant_pali_1", "dps_sbs_chant_eng_1", "dps_sbs_chapter_1", "dps_sbs_source_2", "dps_sbs_sutta_2", "dps_sbs_example_2", "dps_sbs_chant_pali_2", "dps_sbs_chant_eng_2", "dps_sbs_chapter_2", "dps_sbs_source_3", "dps_sbs_sutta_3", "dps_sbs_example_3", "dps_sbs_chant_pali_3", "dps_sbs_chant_eng_3", "dps_sbs_chapter_3", "dps_sbs_source_4", "dps_sbs_sutta_4", "dps_sbs_example_4", "dps_sbs_chant_pali_4", "dps_sbs_chant_eng_4", "dps_sbs_chapter_4", "dps_sbs_class_anki", "dps_sbs_class", "dps_sbs_category", "dps_sbs_patimokkha"]

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
        location=(250, 0),
        size=(900, 1000)
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


# Buttons ex_1, 2, 3 and 4 in DPS
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


# remove buttons on 4 sbs_examples
def remove_sbs_example(example_num, window):

    fields = ['source', 'sutta', 'example', 'chant_pali', 'chant_eng', 'chapter']

    # Update the fields in the GUI to be empty.
    for field in fields:
        key = f'dps_sbs_{field}_{example_num}'
        window[key].update('')  # Remove the content of the field in the GUI.


# Buttons sbs_ex_1, 2, 3 and 4 in DPS
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


# "stash" button DPS
def stash_values_from(dpspth, values, num, window, error_field):
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
        with open(dpspth.dps_stash_path, "w") as f:
            json.dump(values_to_stash, f)
        print(f"Stashed values to {dpspth.dps_stash_path}.")
    except Exception as e:
        print(f"Error while stashing: {e}")
        window[error_field].update(f"Error while stashing: {e}")


# "unstash" button DPS
def unstash_values_to(dpspth, window, num, error_field):
    print("Starting unstash_values_to...")

    window[error_field].update("")
    
    # Check if the stash file exists
    if not os.path.exists(dpspth.dps_stash_path):
        window[error_field].update("Stash file not found!")
        print(f"Error: {dpspth.dps_stash_path} not found.")
        return

    # Load the stashed values
    try:
        with open(dpspth.dps_stash_path, "r") as f:
            unstashed_values = json.load(f)
        print(f"Loaded values from {dpspth.dps_stash_path}: {unstashed_values}")
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


# openai gpt related
def translate_with_openai(dpspth, meaning_in, lemma_1, grammar, pos, notes, suggestion_field, error_field, window, values, mode, main_sentence, model="3", ex_1="", ex_2="", ex_3="", ex_4="", number="0", synonyms=False):
    window[error_field].update("")
    # Get the content of window "meaning_in"
    meaning = values[meaning_in]

    pos_example_map = load_translaton_examples(dpspth)
    translation_example = pos_example_map.get(pos, "")

    model = "gpt-4o-2024-08-06" if model == "4" else "gpt-4o-mini"
    grammar_orig = grammar
    grammar = replace_abbreviations(grammar)

    # Choosing sentence
    sentence = main_sentence if number == "0" else [ex_1, ex_2, ex_3, ex_4][int(number) - 1]
    # print(f"Sentence {sentence}")

    if mode == "meaning":
        messages = generate_messages_for_meaning(lemma_1, grammar, meaning, sentence, translation_example, synonyms)
    elif mode == "note":
        messages = generate_messages_for_notes(lemma_1, grammar, notes)
    elif mode == "english":
        messages = generate_messages_for_english_meaning(lemma_1, grammar, sentence)
    else:
        raise ValueError(f"Invalid mode: {mode}")
    # print(f"messages {messages}")


    # Lazy initialization of OpenAI client
    client = get_openai_client()
    suggestion, error_string = handle_openai_response(client, messages, model)

    if error_string:
        window[error_field].update(error_string)
    elif suggestion:
        suggestion_str = suggestion.content if suggestion is not None else ""
        window[suggestion_field].update(suggestion_str, text_color="Aqua")
        if mode == "meaning":
            write_suggestions_to_csv(dpspth.ai_ru_suggestion_history_path, lemma_1, grammar_orig, grammar, meaning, suggestion_str)
        elif mode == "note":
            write_suggestions_to_csv(dpspth.ai_ru_notes_suggestion_history_path, lemma_1, grammar_orig, grammar, notes, suggestion_str)
        elif mode == "english":
            write_suggestions_to_csv(dpspth.ai_en_suggestion_history_path, lemma_1, grammar_orig, grammar, sentence, suggestion_str)
        else:
            raise ValueError(f"Invalid mode: {mode}")


def write_suggestions_to_csv(file_name, lemma_1, grammar_orig, grammar, original, suggestion):
    with open(file_name, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter="\t")
            writer.writerow([lemma_1, grammar_orig, grammar, original, suggestion])


def copy_and_split_content(sugestion_key, meaning_key, lit_meaning_key, error_field, window, values):

    """
    Copies and splits the content of a field based on delimiters.

    Checks if the content of a field is empty, and if so, updates the error field.
    If not empty, splits the content based on the delimiters 'досл.', 'букв.', '|', 'буквально', 'дословно', 'лит.'.
    If a delimiter is found, updates two fields with the content before and after the delimiter.
    If none of the delimiters are found, just updates one field with the original content.
    """
    
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


# russian spellcheck "spelling_button"
def ru_check_spelling(dpspth, field, error_field, values, window):
    spell_checker = SpellCheck(dpspth.ru_user_dict_path)
    correction = spell_checker.check_spelling(values[field])
    
    if correction:
        num_lines = min(len(correction.split('\n')), 5)
        window[error_field].set_size((50, num_lines))  # Adjust the size of the Text element based on the number of lines
        window[error_field].update(correction)
        window["messages"].update(value="ru spelling", text_color="red")

    else:
        window[error_field].set_size((50, 1))  # Reset to default size
        window[error_field].update("")


def ru_add_spelling(dpspth, word):
    with open(dpspth.ru_user_dict_path, "a", encoding='utf-8') as f:
        f.write(f"{word}\n")


def ru_edit_spelling(dpspth):
    subprocess.Popen(
        ["code", dpspth.ru_user_dict_path])


def tail_log():
    subprocess.Popen(["gnome-terminal", "--", "tail", "-n", "+0", "-f", "/home/deva/logs/gui.log"])
    

# from_test_to_add_button
def read_tsv_words(file_path):
    with open(file_path, "r") as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # Skip header row if present
        words = [row[0] for row in reader]
        return words


# "Save GUI" button Words To Add 
def save_gui_state_dps(dpspth, values, words_to_add_list):
    save_state: tuple = (values, words_to_add_list)
    print(f"[green]saving gui state (2), values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")

    # Check if the file exists and create a backup if it does
    if os.path.exists(dpspth.dps_save_state_path):
        backup_path = str(dpspth.dps_save_state_path) + '_backup'
        shutil.copy2(dpspth.dps_save_state_path, backup_path)
        print(f"[yellow]Backed up old state to {backup_path}")
    
    # Save the new state
    with open(dpspth.dps_save_state_path, "wb") as f:
        pickle.dump(save_state, f)


# "Load GUI" button Words To Add 
def load_gui_state_dps(dpspth):
    with open(dpspth.dps_save_state_path, "rb") as f:
        save_state = pickle.load(f)
    values = save_state[0]
    words_to_add_list = save_state[1]
    print(f"[green]loading gui state (2), values:{len(values)}, words_to_add_list: {len(words_to_add_list)}")
    return values, words_to_add_list


# "to simsapa" button Words To Add
def send_sutta_study_request(word, sutta, source):

    try:

        # Construct the sutta_uid by concatenating sutta with source
        sutta_uid = sutta + source

        print(f"sutta_uid: {sutta_uid}")
        print(f"word: {word}")
        # Construct the params dictionary
        params = {
            "sutta_panels": [
                {
                    "sutta_uid": sutta_uid,
                    "find_text": word
                }
            ],
            "lookup_panel": {
                "query_text": word
            }
        }
        
        # Send the POST request
        response = requests.post("http://localhost:4848/sutta_study", json=params)
        
        # Check the response
        if response.status_code == 200:
            print("Request sent successfully.")
        else:
            print("Error:", response.status_code)

    except RequestException as e:
        print(f"An error occurred while sending the request: {e}")



# "Next Word" button DPD
def add_word_from_csv(dpspth, window, flag_next_word, completion, lemma_1_current=""):
    # read csv file and fill lemma_1, meaning_1, pos, construction and notes

    word_data = read_tsv_dict(dpspth.vinaya_tsv_path)

    # count fitting the criteria
    count = 0
    for row in word_data:
        if row.get("proceed") == "":
            count += 1

    window["messages"].update(f"{count} words left", text_color="white")

    # Find the first row with an empty "proceed" column and update it to "y"
    for row in word_data:
        if flag_next_word:
            if row.get("proceed") == "":
                row["proceed"] = completion
                write_tsv_dot_dict(dpspth.vinaya_tsv_path, word_data)
                word_data = read_tsv_dict(dpspth.vinaya_tsv_path)
                for row in word_data:
                    if row.get("proceed") == "":

                        # Update the GUI 'values' dict with new values from the TSV dict
                        window["lemma_1"].update(row.get("lemma_1", ""))
                        window["meaning_1"].update(row.get("meaning_1", ""))
                        window["pos"].update(row.get("pos", ""))
                        window["grammar"].update(row.get("grammar", ""))
                        window["construction"].update(row.get("construction", ""))
                        window["notes"].update(row.get("notes", ""))
                        window["compound_type"].update(row.get("compound_type", ""))
                        window["compound_construction"].update(row.get("compound_construction", ""))

                        original_word = row.get("missing word", "")
                        print(original_word)
                        break
                break
            else:
                original_word = ""
        else:
            if row.get("proceed") == "":
                # Update the GUI 'values' dict with new values from the TSV dict
                window["lemma_1"].update(row.get("lemma_1", ""))
                window["meaning_1"].update(row.get("meaning_1", ""))
                window["pos"].update(row.get("pos", ""))
                window["grammar"].update(row.get("grammar", ""))
                window["construction"].update(row.get("construction", ""))
                window["notes"].update(row.get("notes", ""))
                window["compound_type"].update(row.get("compound_type", ""))
                window["compound_construction"].update(row.get("compound_construction", ""))

                original_word = row.get("missing word", "")
                print(original_word)
                break

    return original_word


def paragraphs_are_similar(paragraph1, paragraph2, threshold):
    """Helper function to check if two paragraphs are similar based on a similarity threshold."""
    matcher = SequenceMatcher(None, paragraph1, paragraph2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold


def take_example_from_archive(dpspth, window, current_id, ex_1, ex_2, ex_3, ex_4, error_field, archived_example_index, threshold=0.9):
    # Clean the error field at the beginning
    window[error_field].set_size((50, 1))
    window[error_field].update("")

    # Read the TSV file data into a dictionary
    word_data = read_tsv_dict(dpspth.sbs_archive)
    input_examples = {ex_1, ex_2, ex_3, ex_4}
    total_examples = 4  # Total number of examples

    # Find the row with the matching "id"
    for row in word_data:
        if row.get("id") == current_id:
            # Extract examples from the row
            sbs_examples = [
                row.get("sbs_example_1"),
                row.get("sbs_example_2"),
                row.get("sbs_example_3"),
                row.get("sbs_example_4"),
            ]

            # Rotate through examples starting from `archived_example_index`
            for i in range(total_examples):
                example_index = (archived_example_index + i) % total_examples
                sbs_example = sbs_examples[example_index]

                # Check if the example is unique and not similar to input examples
                if sbs_example and all(
                    not paragraphs_are_similar(sbs_example, input_example, threshold)
                    for input_example in input_examples
                ):
                    # Update the GUI with the unique example found
                    window["dps_sbs_source_4"].update(row.get(f"sbs_source_{example_index + 1}", ""))
                    window["dps_sbs_sutta_4"].update(row.get(f"sbs_sutta_{example_index + 1}", ""))
                    window["dps_sbs_example_4"].update(sbs_example)
                    window["dps_sbs_chant_pali_4"].update(row.get(f"sbs_chant_pali_{example_index + 1}", ""))
                    window["dps_sbs_chant_eng_4"].update(row.get(f"sbs_chant_eng_{example_index + 1}", ""))
                    window["dps_sbs_chapter_4"].update(row.get(f"sbs_chapter_{example_index + 1}", ""))

                    # Update archived_example_index to start from the next example on the next call
                    archived_example_index = (example_index + 1) % total_examples
                    return archived_example_index  # Return updated index for the next call

            # If no unique example was found, update the error field
            window[error_field].update("No unique examples")
            return archived_example_index  # Return the same index if no examples found

    # If no row matches `current_id`, update the error field
    window[error_field].update("ID not found")
    return archived_example_index


