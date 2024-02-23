"""Functions for:
1. Summarizating ru meaning and literal meaning,
"""

import re
import csv
from db.models import DpdHeadwords, Russian
from tools.paths import ProjectPaths


def make_ru_meaning(i: DpdHeadwords, ru: Russian) -> str:
	"""Compile ru_meaning and literal meaning, or return ru_meaning_raw."""
	if ru.ru_meaning:
		ru_meaning: str = ru.ru_meaning
		if ru.ru_meaning_lit:
			ru_meaning += f"; досл. {ru.ru_meaning_lit}"
		return ru_meaning
	elif ru.ru_meaning_raw:
		return ru.ru_meaning_raw
	else:
		return ""

def make_ru_meaning_html(i: DpdHeadwords, ru: Russian) -> str:
    """Compile html of ru_meaning and literal meaning, or return ru_meaning_raw.
    ru_meaning in <b>bold</b>"""

    if ru.ru_meaning:
        ru_meaning: str = f"<b>{ru.ru_meaning}</b>"
        if ru.ru_meaning_lit:
            ru_meaning += f"; досл. {ru.ru_meaning_lit}"
        return ru_meaning
    else:
        # add bold to ru_meaning_raw, keep досл. plain
        if "; досл." in ru.ru_meaning_raw:
            return re.sub("(.+)(; досл.+)", "<b>\\1</b>\\2", ru.ru_meaning_raw)
        elif ru.ru_meaning_lit:
            return f"<b>{ru.ru_meaning_raw}</b>; досл. {ru.ru_meaning_lit}"
        else:
            return f"<b>{ru.ru_meaning_raw}</b>"


def replace_abbreviations(value, pth: ProjectPaths):
    # Perform basic replacements
    value = value.replace(' or ', ' или ').replace(', from', ', от').replace(' of ', ' от ')
    # Step  1: Read the TSV file and parse it
    abbreviations = {}
    with open(pth.abbreviations_tsv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            if len(row) >=  6 and row[5]:  # Check if the row has a Russian equivalent
                abbreviations[row[0]] = row[5]

    # Step  2: Sort the abbreviations by length in descending order
    sorted_abbreviations = sorted(abbreviations.items(), key=lambda x: len(x[0]), reverse=True)

    # Step   3: Replace abbreviations in value
    # Use regex to match abbreviations, considering variations like "+acc" or "loc abs"
    for abbr, russian in sorted_abbreviations:
        # Escape special characters in the abbreviation
        escaped_abbr = re.escape(abbr)
        # Adjust the regex pattern to match abbreviations with optional "+" prefix and spaces
        pattern = r'\b\+' + escaped_abbr + r'\b|\b' + escaped_abbr + r'\b'
        # Replace the abbreviation with its Russian equivalent
        value = re.sub(pattern, russian, value)

    return value


def ru_make_grammar_line(i: DpdHeadwords, pth: ProjectPaths) -> str:
    """Compile grammar line and replace values with ru"""
    
    grammar = replace_abbreviations(i.grammar, pth)
    if i.neg:
        grammar += f", {replace_abbreviations(i.neg, pth)}"
    if i.verb:
        grammar += f", {replace_abbreviations(i.verb, pth)}"
    if i.trans:
        grammar += f", {replace_abbreviations(i.trans, pth)}"
    if i.plus_case:
        grammar += f" ({replace_abbreviations(i.plus_case, pth)})"
    return grammar


def replace_grammar(value, pth: ProjectPaths):
    # Perform basic replacements
    value = value.replace(' or ', ' или ').replace(', from', ', от').replace(' of ', ' от ')
    # Step  1: Read the TSV file and parse it
    abbreviations = {}
    with open(pth.abbreviations_tsv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            if len(row) >=  6 and row[5]:  # Check if the row has a Russian equivalent
                abbreviations[row[0]] = row[5]

    # Step  2: Sort the abbreviations by length in descending order
    sorted_abbreviations = sorted(abbreviations.items(), key=lambda x: len(x[0]), reverse=True)

    # Step  3: Replace abbreviations in value
    for abbr, russian in sorted_abbreviations:
        value = value.replace(abbr, russian)

    return value


# def ru_degree_of_completion(i):
#     """Return html styled symbol of a word data degree of completion."""
#     if i.meaning_1:
#         if i.source_1:
#             return """<span class="gray">✓</span>"""
#         else:
#             return """<span class="gray">~</span>"""
#     else:
#         return """<span class="gray">✗</span>"""
