
"""Functions for openai"""

import csv
import re

from openai import OpenAI

from rich.prompt import Prompt
from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

from tools.configger import config_test_option, config_read, config_update
from dps.tools.paths_dps import DPSPaths    
from tools.paths import ProjectPaths


dpspth = DPSPaths()
pth = ProjectPaths()


def get_openai_client():
    """Initialize and return an OpenAI client if the API key is configured."""
    try:
        api_key = load_openai_config()
        return OpenAI(api_key=api_key)
    except ValueError as e:
        # Handle cases where OpenAI is not required but key is missing
        print(f"OpenAI client initialization skipped: {e}")
        return None


def load_openai_config():
    """Add a OpenAI key if one doesn't exist, or return the key if it does."""

    if not config_test_option("openai", "key"):
        openai_config = Prompt.ask("[yellow]Enter your openai key (or ENTER for None)")
        if openai_config:
            config_update("openai", "key", openai_config)
        else:
            raise ValueError("OpenAI key is required")
    else:
        openai_config = config_read("openai", "key")

    return openai_config


def load_translaton_examples(dpspth):
    """Load the pos-examples mapping from a TSV file into a dictionary."""
    pos_examples_map = {}
    if dpspth.translation_example_path:
        with open(dpspth.translation_example_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            next(reader)  # Skip header row
            for row in reader:
                pos, examples = row[0], row[1]
                pos_examples_map[pos] = examples
    return pos_examples_map


@timeout(5, timeout_exception=TimeoutDecoratorError)  # Setting a 5-second timeout
def handle_openai_response(client, messages, model):
    if client is None:
        return None, "OpenAI client is not initialized."
        
    error_string = ""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return completion.choices[0].message, error_string
    except TimeoutDecoratorError:
        error_string = "Timed out"
        print(error_string)
    except Exception as e:
        error_string = f"Error: {e}"
        print(error_string)
    return None, error_string


def replace_abbreviations(grammar_string):

    # Clean the grammar string
    cleaned_grammar_string = re.sub(r' of [\w\s]+|, pp of [\w\s]+|, prp of [\w\s]+|, ptp of [\w\s]+|, from [\w\s]+|, loc abs|, gen abs|\(.*?\)', '', grammar_string)

    #! consider noun, pp of ... remove pp or make it from pp

    replacements = {}
    multi_word_replacements = {}

    # Read abbreviations and their full forms into a dictionary
    with open(pth.abbreviations_tsv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = row[0], row[1].split(',')[0].strip()  # select only the first two columns and split by comma
            if ' ' in abbrev:
                multi_word_replacements[abbrev] = full_form
            else:
                replacements[abbrev] = full_form

    # First, replace multi-word abbreviations
    for abbrev, full_form in multi_word_replacements.items():
        cleaned_grammar_string = re.sub(r'\b' + re.escape(abbrev) + r'\b', full_form, cleaned_grammar_string)

    # Then, replace single-word abbreviations
    words = re.findall(r"[\w'+&]+|[.,!?;]", cleaned_grammar_string)
    for idx, word in enumerate(words):
        if word in replacements:
            words[idx] = replacements[word]

    # Join the words back into a string
    replaced_string = ' '.join(words)

    # debug
    # print(f"{grammar_string} || replaced with || {replaced_string}")

    return replaced_string