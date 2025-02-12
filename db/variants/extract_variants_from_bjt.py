"""Extract variants readings from BJT texts."""

import json
import re

from pathlib import Path

from db.variants.variants_modules import key_cleaner
from db.variants.variants_modules import VariantsDict

from tools.paths import ProjectPaths
from tools.printer import p_counter, p_green_title
from tools.tic_toc import bip

debug = False


def get_bjt_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of BJT json files."""

    bjt_json_dir: Path = pth.bjt_roman_json_dir
    files: list[Path] = sorted([f for f in bjt_json_dir.iterdir() if f.is_file()])
    return files


def get_bjt_json_data(file_path: Path) -> dict: # the dict has an overcomplicated structure, impossible to type
    """Get the JSON data from the file_path"""

    with open(file_path, "r", encoding="UTF-8") as f:
        return json.load(f)


def extract_bjt_variants(
    file_name: Path,
    variants_dict: VariantsDict,
    errors_list: list
) -> tuple[VariantsDict, list[tuple]]:
    """Extract variants from a BJT json file."""

    json_data = get_bjt_json_data(file_name)
    book = re.sub(r"-\d+.*", "", file_name.stem)
    pages = json_data['pages']

    # compile vars for each page
    for page in pages:

        page_num = page["pageNum"] 
        pali = page["pali"]
        entries = pali["entries"]
        footnotes = pali["footnotes"]

        page_variants_dict = {}
        page_footnotes_dict = {}
        
        # find all the {1} or {*} in text
        # and compile into a local dict
        for entry in entries:
            text = entry["text"]
            var_capture = re.findall(
                r"""        
                (^|\n| )    # starts with para, newline or space
                ([^\n ]*    # 0 or more characters without space or \n = capture group1 
                \s*)        # optional space
                \{          # open curly brackets
                ([0-9*]+?)  # 1 or more digits or * = capture group2 
                \}          # close curly braces
                """,
                text,       # find in text
                re.VERBOSE  # otherwise it doesn't work
            )
            for var_c in var_capture:
                start, word, number = var_c
                page_variants_dict[number] = word

        # find all the {1} or {*} in footnotes
        # and compile into a local dict
        for footnote in footnotes:
            text = footnote["text"]
            fn_capture = re.findall(
                r"""        
                ([0-9*]+)   # 1 or more digits or * in cgroup1
                \.\s        # literal full-stop space
                (.+)        # everything til the end in cgroup2
                """,
                text,       # find in text
                re.VERBOSE | # otherwise it doesn't work 
                re.DOTALL
            )
            for fnc in fn_capture:
                number, definition = fnc
                page_footnotes_dict[number] = definition

        # compile page variants into variants_dict
        for key, word in page_variants_dict.items():
            word_clean = key_cleaner(word)

            try:
                definition = page_footnotes_dict[key]

                # ensure outer dictionary entry exists
                if word_clean not in variants_dict:
                    variants_dict[word_clean] = {}
                
                # ensure cst entry exists
                if "BJT" not in variants_dict[word_clean]:
                    variants_dict[word_clean]["BJT"] = {}

                # ensure inner dictionary entry exists
                if book not in variants_dict[word_clean]["BJT"]:
                    variants_dict[word_clean]["BJT"][book] = []

                if definition not in variants_dict[word_clean]["BJT"][book]:
                    variants_dict[word_clean]["BJT"][book].append(definition)

            except KeyError:
                pass
                errors_list.append((file_name.stem, page_num, key))

        # also find the opposite kind of error
        for key, word_clean in page_footnotes_dict.items():
            try:
                definition = page_variants_dict[key]
            except KeyError:
                if "__"  not in word_clean:
                    errors_list.append((file_name.stem, page_num, key))

    return variants_dict, errors_list


def bjṭ_footnote_errors(errors_list):
    p_green_title("bjt footnote errors")
    print("|File Name|Page|Footnote|")
    print("|:---|:---|:---|")
    for e in errors_list:
        file_name, page_num, key = e
        print(f"|{file_name}|{page_num}|{key}|")


def process_bjt(
        variants_dict: VariantsDict,
        pth: ProjectPaths
) -> VariantsDict:
    
    p_green_title("extracting variants from BJT texts")

    errors_list = []

    file_list: list[Path] = get_bjt_file_list(pth)

    bip()
    for counter, file_name in enumerate(file_list):

        if counter % 30 == 0:
            p_counter(counter, len(file_list), file_name.name)
            bip()
        
        variants_dict, errors_list = extract_bjt_variants(
            file_name, variants_dict, errors_list)
    
    if debug:
        bjṭ_footnote_errors(errors_list)

    return variants_dict
    