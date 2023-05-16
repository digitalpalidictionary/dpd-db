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
from tools.pali_text_files import mula_books, all_books
from tools.paths import ProjectPaths as PTH


def make_cst_text_set(books: list, niggahita="ṃ", return_list=False) -> set:
    """Make a list of words in CST texts from a list of books.
    Return a list or a set."""

    cst_texts_list = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: list = []

    for book in cst_texts_list:
        with open(PTH.cst_txt_dir.joinpath(book), "r") as f:
            text_string = f.read()
            text_string = clean_machine(text_string, niggahita=niggahita)
            words_list.extend(text_string.split())

    if return_list is True:
        return words_list
    else:
        return set(words_list)


def make_sc_text_set(books: list, niggahita="ṃ", return_list=False) -> set:
    """Make a list of words in Sutta Central texts from a list of books.
    Return a list or a set."""

    # make a list of file names of included books
    sc_texts_list: list = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            print(f"[red]book does not exist: {e}")
            return set()

    words_list: list = []

    for root, dirs, files in sorted(os.walk(PTH.sc_dir)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file)) as f:
                    # sc texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for title, text in sc_text_dict.items():
                        clean_text = clean_machine(text, niggahita=niggahita)
                        words_list.extend(clean_text.split())

    if return_list is True:
        return words_list
    else:
        return set(words_list)


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


def make_mula_words_set():
    """Returns a set of all words in cst & sc mūla texts.
    Usage: mula_word_set = make_mula_words_set()"""
    cst_word_set = make_cst_text_set(mula_books)
    sc_word_set = make_sc_text_set(mula_books)
    mula_word_set = cst_word_set | sc_word_set
    return mula_word_set


def make_all_words_set():
    """Returns a set of all words in cst & sc texts.
    Usage: all_words_set = make_all_words_set()"""
    cst_word_set = make_cst_text_set(all_books)
    sc_word_set = make_sc_text_set(all_books)
    all_words_set = cst_word_set | sc_word_set
    return all_words_set
