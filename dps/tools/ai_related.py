"""Functions for openai"""

import csv
import re

from tools.ai_deepseek_manager import DeepseekManager
from openai import OpenAI

from rich.prompt import Prompt
from timeout_decorator import timeout, TimeoutError as TimeoutDecoratorError

from tools.configger import config_test_option, config_read, config_update
from dps.tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths


dpspth = DPSPaths()
pth = ProjectPaths()


def get_ai_client(provider: str):
    """Initialize and return an AI client for specified provider."""
    try:
        api_key = load_ai_config(provider)
        if provider == "deepseek":
            return DeepseekManager(api_key=api_key)
        elif provider == "openai":
            return OpenAI(api_key=api_key)
        raise ValueError(f"Unsupported provider: {provider}")
    except ValueError as e:
        print(f"{provider.title()} client initialization failed: {e}")
        return None


def load_ai_config(provider: str):
    """Load API key for specified provider from config or prompt user."""

    if not config_test_option("apis", provider):
        ai_key = Prompt.ask(
            f"[yellow]Enter your {provider} API key (or ENTER for None)"
        )
        if ai_key:
            config_update("apis", provider, ai_key)
        else:
            raise ValueError(f"{provider} API key is required")
    else:
        ai_key = config_read("apis", provider)

    return ai_key


def load_translation_examples(dpspth):
    """Load the pos-examples mapping from a TSV file into a dictionary."""
    pos_examples_map = {}
    if dpspth.translation_example_path:
        with open(dpspth.translation_example_path, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            next(reader)  # Skip header row
            for row in reader:
                pos, examples = row[0], row[1]
                pos_examples_map[pos] = examples
    return pos_examples_map


@timeout(10, timeout_exception=TimeoutDecoratorError)  # Setting a 10-second timeout
def handle_ai_response(client, messages, model, provider: str):
    if client is None:
        return None, "client is not initialized."

    error_string = ""
    try:
        if provider == "openai":
            response = client.chat.completions.create(model=model, messages=messages)
            content = response.choices[0].message.content
        elif provider == "deepseek":
            prompt = [{"content": m["content"], "role": m["role"]} for m in messages]
            response = client.chat(
                prompt=prompt, model=model, stream=False, max_tokens=4096
            )
            content = response
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        return {"content": content}, error_string
    except TimeoutDecoratorError:
        error_string = "Timed out"
    except Exception as e:
        error_string = f"{provider.title()} Error: {e}"

    print(error_string)
    return None, error_string


def replace_abbreviations(grammar_string):
    # Clean the grammar string
    cleaned_grammar_string = re.sub(
        r" of [\w\s]+|, pp of [\w\s]+|, prp of [\w\s]+|, ptp of [\w\s]+|, from [\w\s]+|, loc abs|, gen abs|\(.*?\)",
        "",
        grammar_string,
    )

    # TODO consider noun, pp of ... remove pp or make it from pp

    replacements = {}
    multi_word_replacements = {}

    # Read abbreviations and their full forms into a dictionary
    with open(pth.abbreviations_tsv_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter="\t")
        next(reader)  # skip header
        for row in reader:
            abbrev, full_form = (
                row[0],
                row[1].split(",")[0].strip(),
            )  # select only the first two columns and split by comma
            if " " in abbrev:
                multi_word_replacements[abbrev] = full_form
            else:
                replacements[abbrev] = full_form

    # First, replace multi-word abbreviations
    for abbrev, full_form in multi_word_replacements.items():
        cleaned_grammar_string = re.sub(
            r"\b" + re.escape(abbrev) + r"\b", full_form, cleaned_grammar_string
        )

    # Then, replace single-word abbreviations
    words = re.findall(r"[\w'+&]+|[.,!?;]", cleaned_grammar_string)
    for idx, word in enumerate(words):
        if word in replacements:
            words[idx] = replacements[word]

    # Join the words back into a string
    replaced_string = " ".join(words)

    # debug
    # print(f"{grammar_string} || replaced with || {replaced_string}")

    return replaced_string


def generate_messages_for_meaning(
    lemma_1, grammar, meaning, sentence, translation_example="", synonyms=False
):
    """Generate messages for translation."""

    system_content = "You are a skilled assistant that translates English text to Russian with grammatical accuracy, contextual relevance, and strict adherence to rules."

    user_content = f"""
        Translate the English definition of the Pali term into Russian, following these rules:

        - Translate all bracketed text (e.g., "(gram)" → "(грам)", "(comm)" → "(комм)", "(vinaya)" → "(виная)", "(of weather)" → "(о погоде)").
        - Separate synonyms with `;`.
        - Match the grammatical structure of the Pali term (noun, verb, etc.).
        - Use lowercase unless it's a proper noun.
        - Translate "lit." as "досл.".
        - Retain clarifications if any (e.g., "(of trap) laid down" → "(о капкане) установленный").
        - Translate idioms to Russian equivalents.
        - Ensure no English remains untranslated, including within brackets.
        - Output only the translation of the Definition, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

        **Pali Term**: {lemma_1}
        **Grammar**: {grammar}
        **Definition**: {meaning}
    """

    if sentence:
        user_content += f"\n- Consider Pali context: {sentence}"

    if translation_example:
        user_content += f"\n- Match this example format: {translation_example}"

    if synonyms:
        user_content = user_content.replace(
            "Translate the English definition of the Pali term into Russian",
            "Provide at least nine (9) distinct Russian synonyms for the English definition of Pali term",
        )

    # print(user_content)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_messages_for_notes(lemma_1, grammar, notes):
    """Generate messages for translation."""

    system_content = "You are a helpful assistant that translates English text to Russian considering the context."

    user_content = f"""
    Translate the English notes into Russian, following these rules:
    - Keep Pali or Sanskrit terms in roman script.
    - Output only the translation of the Notes, without labels like "Перевод" etc, without any comments, without translation of the Grammar and in one line.

                **Pali Term**: {lemma_1}
                **Grammar**: {grammar}
                **Notes**: {notes}
    """

    # print(user_content)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def generate_messages_for_english_meaning(lemma_1, grammar, sentence):
    """Generate messages for translation."""

    system_content = "You are a helpful assistant that translates Pali to English considering the context."

    user_content = f"""

    Given the grammatical and contextual details provided, list at least 8 distinct English synonyms for the specified Pali term. Avoid repeating the same word. In the answer provide only a list of synonyms separated by ';' without any introduction or comments.

                **Pali Term**: {lemma_1}
                **Grammar**: {grammar}
                **Context**: {sentence}
    """

    # print(user_content)
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
