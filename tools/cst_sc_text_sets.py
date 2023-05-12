"""Make sets of clean words in Chaṭṭha Saṅgāyana and Sutta Central texts.
How to use: feed and a list of books and get a set in return.
cst_test_set = make_cst_text_set(["an1", "an2"])
sc_text_set = make_sc_text_set(["abh7"])
sc_text_set = make_sc_text_set(["an1"], niggahita="ṁ")
"""

import os
import json

from rich import print

from tools.clean_machine import clean_machine
from tools.pali_text_files import sc_texts, cst_texts, bjt_texts
from tools.paths import ProjectPaths as PTH


def make_cst_text_set(books: list, niggahita="ṃ") -> set:

    cst_texts_list = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    cst_text_set = set()

    for book in cst_texts_list:
        with open(PTH.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            text_string = clean_machine(text_string, niggahita=niggahita)
            text_set = text_string.split()
            cst_text_set.update(text_set)

    return cst_text_set


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

    sc_text_set: set = set()

    for root, dirs, files in sorted(os.walk(PTH.sc_dir)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # sc texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for title, text in sc_text_dict.items():
                        clean_text = clean_machine(text, niggahita=niggahita)
                        sc_text_set.update(clean_text.split())

    return sc_text_set


def make_bjt_text_set(include):

    print(f"[green]{'making buddhajayanti text set':<35}", end="")

    bjt_texts_list = []
    for i in include:
        if bjt_texts[i]:
            bjt_texts_list += bjt_texts[i]

    bjt_text_string = ""

    for bjt_text in bjt_texts_list:
        with open(PTH.bjt_text_path.joinpath(bjt_text), "r") as f:
            bjt_text_string += f.read()

    bjt_text_string = clean_machine(bjt_text_string)
    bjt_text_set = set(bjt_text_string.split())

    print(f"[white]{len(bjt_text_set):>10,}")
    return bjt_text_set
