"""Extract variants readings from Sutta Central texts."""

import json
import re
from pathlib import Path

from db.variants.files_to_books import mst_files_to_books
from db.variants.variants_modules import VariantsDict, key_cleaner
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def get_sc_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of all SC variants files."""

    root_dir = pth.sc_variants_dir
    file_list = [file for file in root_dir.rglob("*") if file.is_file()]

    # Create a list of (book_order, filename) tuples
    sorted_files = []
    for file in file_list:
        # Find first matching book key
        for order, (key, book) in enumerate(mst_files_to_books.items()):
            if file.name.startswith(key):
                sorted_files.append((order, file))
                break
        else:  # No match found
            sorted_files.append(
                (len(mst_files_to_books), file)
            )  # Push non-matches to end

    # Sort by book order then filename
    sorted_files.sort(key=lambda x: (x[0], x[1]))
    sorted_files = [f[1] for f in sorted_files]

    for sf in sorted_files:
        print(sf.name)
    return sorted_files


def get_json_data(file_path: Path) -> dict[str, str]:
    """Get the JSON data from the file_path"""

    with open(file_path, "r", encoding="UTF-8") as f:
        return json.load(f)


def extract_sc_variants(
    json_data: dict[str, str], variants_dict: VariantsDict, book: str
) -> VariantsDict:
    """ "Extract variants from a SC json file."""

    for reference_code, data in json_data.items():
        # data is a list of items separated by '|'
        data_list = data.split("|")

        for d in data_list:
            d = d.strip()
            d = d.replace("ṁ", "ṃ")

            # root_word / variants pairs are separated by '→'
            variants_list = [part.strip() for part in d.split("→", maxsplit=1)]

            # normal case
            if len(variants_list) == 2:
                word, variants = variants_list
                word_clean = key_cleaner(word)

            # fallback case where there is no '→'
            else:
                variants = variants_list[0]

            # sometimes there are multiple variants separated by ';'
            for variant in variants.split(";"):
                # ensure outer dictionary entry exists
                if word_clean not in variants_dict:
                    variants_dict[word_clean] = {}

                # ensure MST entry exists
                if "MST" not in variants_dict[word_clean]:
                    variants_dict[word_clean]["MST"] = {}

                # ensure inner dictionary entry exists
                if book not in variants_dict[word_clean]["MST"]:
                    variants_dict[word_clean]["MST"][book] = []

                variants_dict[word_clean]["MST"][book].append(
                    (word.lower(), variant.strip())
                )

    return variants_dict


def get_book_name(file_name: Path):
    for code, book in mst_files_to_books.items():
        if file_name.name.startswith(code):
            return book
    pr.red(file_name.name)


def process_sc(variants_dict: VariantsDict, pth: ProjectPaths) -> VariantsDict:
    pr.green_title("extracting variants from SC texts")

    file_list: list[Path] = get_sc_file_list(pth)

    for counter, file_name in enumerate(file_list):
        if counter % 500 == 0:
            pr.counter(counter, len(file_list), file_name.name)

        json_data = get_json_data(file_name)
        book = get_book_name(file_name)
        variants_dict = extract_sc_variants(json_data, variants_dict, book)

    return variants_dict
