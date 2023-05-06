"""Make sets of clean words in Chaṭṭha Saṅgāyana and Sutta Central texts.
How to use: feed and a list of books and get a set in return.
cst_test_set = make_cst_text_set(["an1", "an2"])
sc_text_set = make_sc_text_set(["abh7"])
sc_text_set = make_sc_text_set(["an1"], niggahita="ṁ")
"""

import os
import json

from pathlib import Path
from rich import print

from tools.clean_machine import clean_machine
from tools.pali_text_files import sc_texts, cst_texts


def make_cst_text_set(books: list, niggahita="ṃ") -> set:

    cst_text_path = Path("resources/tipitaka-xml/roman_txt/")
    cst_texts_list = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    cst_text_set = set()
    cst_text_string = ""

    for book in cst_texts_list:
        with open(cst_text_path.joinpath(book), "r") as f:
            text_string = f.read()
            text_string = clean_machine(text_string, niggahita=niggahita)
            text_set = text_string.split()
            cst_text_set.update(text_set)
            cst_text_string += text_string

            # # details
            # print(f"{book:<20}", end=" ")
            # print(f"{len(text_set):>10,}", end=" ")
            # print(f"{len(cst_text_set):>10,}")

    return cst_text_set, cst_text_string


def make_sc_text_set(books: list, niggahita="ṃ") -> set:
    """Make a set of words in Sutta Central texts based on a list of books."""

    # make a list of file names of included books
    sc_texts_list: list = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            print(f"[red]book does not exist: {e}")
            return set()

    # make set of words in those files
    path = "resources/sutta central/"
    sc_text_set: set = set()

    for root, dirs, files in sorted(os.walk(path)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # sc texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for title, text in sc_text_dict.items():
                        clean_text = clean_machine(text, niggahita=niggahita)
                        sc_text_set.update(clean_text.split())

    return sc_text_set


# print("unique\twords\tcharacters")
# cst_text_set, cst_text_string = make_cst_text_set(["dn1", "dn2", "dn3"])
# print(f"{len(cst_text_set):,}\t{len(cst_text_string.split()):,}\t{len(cst_text_string):,}")

# cst_text_set, cst_text_string = make_cst_text_set(["dna"])
# print(f"{len(cst_text_set):,}\t{len(cst_text_string.split()):,}\t{len(cst_text_string):,}")

# cst_text_set, cst_text_string = make_cst_text_set(["dnt"])
# print(f"{len(cst_text_set):,}\t{len(cst_text_string.split()):,}\t{len(cst_text_string):,}")

# sc_text_set = make_sc_text_set(["an1"], niggahita="ṁ")
