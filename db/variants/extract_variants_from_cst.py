"""Extract variants readings from CST texts."""

import re
from bs4 import BeautifulSoup
from icecream import ic
from pathlib import Path

from db.variants.variants_modules import context_cleaner, key_cleaner
from db.variants.variants_modules import VariantsDict
from db.variants.files_to_books import cst_files_to_books

from tools.paths import ProjectPaths
from tools.printer import printer as pr

debug = False


def get_cst_file_list(pth: ProjectPaths) -> list[Path]:
    """Get a list of CST files."""

    cst_xml_dir: Path = pth.cst_xml_dir
    files: list[Path] = sorted(
        [f for f in cst_xml_dir.iterdir() if f.is_file()],
        key=lambda x: list(cst_files_to_books.keys()).index(x.name),
    )

    return files


def make_soup(file: Path) -> BeautifulSoup:
    """Make a soup from a CST file."""

    with open(file, "r", encoding="UTF-16") as f:
        file_contents: str = f.read()
        soup: BeautifulSoup = BeautifulSoup(file_contents, "xml")

        # remove all the "pb" tags
        pbs = soup.find_all("pb")
        for pb in pbs:
            pb.decompose()

        # remove all the hi paranum dot tags
        his = soup.find_all("hi", rend=["paranum", "dot"])
        for hi in his:
            hi.unwrap()

        return soup


def extract_variants(
    soup: BeautifulSoup, variants_dict: VariantsDict, book_name: str
) -> VariantsDict:
    """Extract variants from a CST file."""

    notes = soup.find_all("note")
    for note in notes:
        # Get preceding text node
        preceding_text = note.previous_sibling

        if preceding_text and not preceding_text.text.strip():
            preceding_text = note.previous_sibling.previous_sibling  # type: ignore

        if preceding_text:
            text_str: str = preceding_text.text.strip()
            if text_str:
                # Split text into words and get last word before note
                words: list[str] = text_str.split()

                if words:
                    word = words[-1]
                    word_clean: str = key_cleaner(word)

                    # get context for the word
                    if len(words) > 1:
                        # use the last two words for context
                        context: str = " ".join(words[-2:]).lower()
                    else:
                        # just use the last word for context
                        context: str = word.lower()
                    context_clean = context_cleaner(context)

                    variants: str = note.get_text(strip=True)

                    if debug:
                        ic(context, word_clean, variants)
                        input()

                    # separate on closing parenthesis followed by whitespace
                    # e.g. a (a) b (b) c (c)
                    # but not if there are no brackets at the end
                    # e.g. a (a) b
                    variants_split = re.split(
                        r"""
                        (?<=\))      # Lookbehind for closing bracket
                        ,*           # Optional comma
                        \s+          # One or more whitespace characters
                        (?=          # Lookahead for...
                            \S+      # One or more non-whitespace characters
                            \s*      # Optional whitespace
                            \(       # Opening bracket
                        )
                        """,
                        variants,
                        flags=re.VERBOSE,
                    )

                    if debug:
                        if len(variants_split) > 1:
                            ic(word_clean)
                            ic(variants)
                            ic(variants_split)
                            print()

                    for variant in variants_split:
                        variant = variant.strip()

                        if variant == "( )":
                            continue

                        # ensure outer dictionary entry exists
                        if word_clean not in variants_dict:
                            variants_dict[word_clean] = {}

                        # ensure CST entry exists
                        if "CST" not in variants_dict[word_clean]:
                            variants_dict[word_clean]["CST"] = {}

                        # ensure inner dictionary entry exists
                        if book_name not in variants_dict[word_clean]["CST"]:
                            variants_dict[word_clean]["CST"][book_name] = []

                        variants_dict[word_clean]["CST"][book_name].append(
                            (context_clean, variant)
                        )

    return variants_dict


def process_cst(variants_dict: VariantsDict, pth: ProjectPaths) -> VariantsDict:
    pr.green_title("extracting variants from CST texts")
    files: list[Path] = get_cst_file_list(pth)

    for counter, file_name in enumerate(files):
        if counter % 25 == 0:
            pr.counter(counter, len(files), file_name.name)

        if debug:
            if counter == 20:
                break

        soup: BeautifulSoup = make_soup(file_name)

        # remove .mul .att .tik from book names
        book_name = cst_files_to_books[file_name.name]

        variants_dict = extract_variants(soup, variants_dict, book_name)

    return variants_dict
