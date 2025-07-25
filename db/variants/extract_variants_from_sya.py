# -*- coding: utf-8 -*-
"""Extract variants readings from Syāmaraṭṭḥa (Thai) texts."""

import re
from pathlib import Path

from icecream import ic

from db.variants.files_to_books import sya_files_to_books
from db.variants.variants_modules import VariantsDict, context_cleaner, key_cleaner
from tools.paths import ProjectPaths
from tools.printer import printer as pr

debug = False

global errors
errors: int = 0
global successes
successes: int = 0


def process_sya(variants_dict: VariantsDict, pth: ProjectPaths) -> VariantsDict:
    pr.green_title("extracting variants from SYA texts")

    file_list: list[Path] = get_sya_file_list(pth)

    for counter, file_name in enumerate(file_list):
        if counter % 20 == 0:
            pr.counter(counter, len(file_list), file_name.name)

        book = sya_files_to_books[file_name.name]
        text = get_sya_text(file_name)
        variants_dict = extract_sya_variants(book, text, variants_dict)

    error_rate = (errors / successes) * 100
    pr.red(f"extracted:  {successes - errors} / {successes}")
    pr.red(f"error rate: {error_rate:.2}%")

    return variants_dict


def get_sya_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of all SYA variants files."""

    root_dir = pth.sya_dir
    sya_sort_order = {filename: idx for idx, filename in enumerate(sya_files_to_books)}
    all_files = [file for file in root_dir.rglob("*") if file.is_file()]
    file_list = sorted(
        all_files,
        key=lambda x: sya_sort_order.get(x.name, float("inf")),
    )
    return file_list


def get_sya_text(file_name: Path) -> str:
    with open(file_name, "r", encoding="UTF-8") as f:
        text = f.read()

        # remove new lines
        text = text.replace("\n", " ")

        # remove page numbers < PTS. Vin III , 87 >
        text = re.sub(r"<.+?>", "", text)

        # remove multiple space
        text = re.sub(" +", " ", text)

        text = text.replace("ṁ", "ṃ")

        return text


def get_page_number(i: int, page: str) -> int:
    """Find the page number."""

    match = re.search(r"\[page (\d+)\]", page)
    if match:
        return int(match.group(1))
    else:
        return 0


def extract_sya_variants(
    book: str, text: str, variants_dict: VariantsDict
) -> VariantsDict:
    """ "Extract variants from a SYA text file."""

    # split on [page xyz]
    pages = re.split(r"(?=\[page \d+\])", text)

    for i, page in enumerate(pages):
        page_num: int = get_page_number(i, page)
        page_vars = get_variants_in_page(page)
        footnote_vars = get_variants_in_footnotes(page)

        if len(footnote_vars) != len(page_vars):
            global errors
            errors += 1
            if debug:
                ic(book)
                ic(page_num)
                ic(page_vars)
                ic(footnote_vars)
                ic(len(footnote_vars) == len(page_vars))
                print()

        for var_num, context in page_vars.items():
            word = context.split(" ")[-1]
            word_clean = key_cleaner(word)
            context_clean = context_cleaner(context)

            try:
                variant = footnote_vars[var_num].strip()
            except KeyError:
                if debug:
                    ic("missing footnote")
                    ic(book)
                    ic(word_clean)
                    ic(var_num)
                    print()
                continue

            # ensure outer dictionary entry exists
            if word_clean not in variants_dict:
                variants_dict[word_clean] = {}

            # ensure SYA entry exists
            if "SYA" not in variants_dict[word_clean]:
                variants_dict[word_clean]["SYA"] = {}

            # ensure inner dictionary entry exists
            if book not in variants_dict[word_clean]["SYA"]:
                variants_dict[word_clean]["SYA"][book] = []

            variants_dict[word_clean]["SYA"][book].append(
                (context_clean, variant.lower())
            )
            global successes
            successes += 1

    return variants_dict


def get_variants_in_page(text: str) -> dict[str, str]:
    """Find variants in the page"""

    # up to two words followed by space digit dash
    # buddhā 1- bhagavanto ahesuṁ sāvake 2- cetasā

    page_vars: dict[str, str] = {}
    pattern = r"""
        (
            (?:[^ ]+\s+)?   # optional first word followed by space
            [^ ]+           # one or more characters without space (capture group 1)
        )                   
        \s                  # a space
        \[*                 # 0+ opening square brackets 
        (\d+)               # 1+ digits (capture group 2)
        \]*            # 0+ closing square brackets 
        -              # dash
        """
    matches = re.findall(pattern, text, re.VERBOSE)
    for context, number in matches:
        page_vars[number] = context
    return page_vars


def clean_variant(text: str) -> str:
    """remove -------"""
    return re.sub("-{3,}", "", text).strip()


def get_variants_in_footnotes(page: str) -> dict[str, str]:
    """Find variants in the footnotes"""

    # Footnote:1 ayaṁ pāṭho katthaci na dissati. 2 sāvakānantipi atthi.

    footnote_vars: dict[str, str] = {}

    # isolate the footnote section
    pattern = r"Footnote:(.*?)(?=\n-{2,}|$)"
    match = re.search(pattern, page, flags=re.DOTALL)
    if match:
        footnote_str = match.group(1).strip()

        # split on 0+ dot behind / 1 or more spaces / number ahead
        footnotes = re.split(r"(?<=\.)* +(?=\d)", footnote_str)
        for footnote in footnotes:
            # footnote contains a triple range e.g.
            # 3-4-5 yamidha sañjotibhūtā sañjotibhūto sañjotibhūtanti likhiyati
            if re.findall(r"\d+-\d+-\d+", footnote):
                pattern = r"(\d+)-\d+-(\d+)"
                match = re.findall(pattern, footnote)
                if match:
                    start, end = match[0]
                    if start and end:
                        variant = re.sub(r"(\d+)-(\d+)", "", footnote)
                        variant = clean_variant(variant)
                        for i in range(int(start), int(end) + 1):
                            footnote_vars[str(i)] = variant
                            if debug:
                                ic(str(i), variant)
                                print()

            # footnote contains a number range e.g.
            # 1-3 Yu. Ma. arahattaṁ.
            if re.findall(r"\d+-\d+", footnote):
                pattern = r"(\d+)-(\d+)"
                match = re.findall(pattern, footnote)
                if match:
                    start, end = match[0]
                    if start and end:
                        variant = re.sub(r"(\d+)-(\d+)", "", footnote)
                        variant = clean_variant(variant)
                        for i in range(int(start), int(end) + 1):
                            footnote_vars[str(i)] = variant
                            if debug:
                                ic(str(i), variant)
                                print()

            # normal situation
            else:
                pattern = r"^(\d+)\s(.+)"
                matches = re.findall(pattern, footnote)
                for match in matches:
                    number, variant = match
                    variant = clean_variant(variant)
                    footnote_vars[number] = variant

    return footnote_vars


# TODO issues
# -* in text and footnotes
# missing footnotes in text
