# -*- coding: utf-8 -*-
"""Make sets of clean words in Chaṭṭha Saṅgāyana and Sutta Central texts.
Optionally change the niggahita character.
How to use: feed in a list of books and get a set in return.
    cst_test_set = make_cst_text_set(["an1", "an2"])
    sc_text_set = make_sc_text_set(["abh7"])
    sc_text_set = make_sc_text_set(["an1"], niggahita="ṁ")
"""

import json
import os
import re
from rich import print

from tools.clean_machine import clean_machine
from tools.pali_text_files import all_books, cst_texts, mula_books, sc_texts
from tools.paths import ProjectPaths
from tools.printer import printer as pr

pth: ProjectPaths = ProjectPaths()


def make_cst_text_set(
    pth: ProjectPaths,
    books: list[str],
    niggahita="ṃ",
    add_hyphenated_parts=True,
) -> set[str]:
    """
    Make a set of words in CST texts from a list of books.
    - Use when keeping the word order is *not* important.
    - Optionally change the niggahita character (niggahita="ṃ" or niggahita="ṁ")
    - Optionally add the parts of hyphenated word (add_hyphenated_parts=True)
    - Return a disordered set.
    """
    pr.green_tmr("making cst text set")
    cst_texts_list: list[str] = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: list[str] = []

    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r", encoding="utf-8") as f:
            text_string = f.read()
            if add_hyphenated_parts:
                # dont remove the hyphen, deal with it later
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=False
                )
            else:
                # remove the hyphen immediately
                text_string = clean_machine(
                    text_string, niggahita=niggahita, remove_hyphen=True
                )

            words_list.extend(text_string.split())

    words_list = list(set(words_list))

    if add_hyphenated_parts:
        words_list = hyphenated_parts_adder(words_list)

    pr.yes(len(set(words_list)))
    return set(words_list)


def hyphenated_parts_adder(words_list: list[str]) -> list[str]:
    for index, word in enumerate(words_list):
        if "-" in word:
            # remove the dash and add the clean word back into the list
            words_list[index] = word.replace("-", "")

            # split on dashes and add each split back into the list
            # in the correct order
            hyphenated_words = word.split("-")
            for h_word in hyphenated_words.__reversed__():
                words_list.insert(index + 1, h_word)
    return words_list


def make_cst_text_list(
    books: list[str],
    niggahita="ṃ",
    dedupe=True,
    add_hyphenated_parts=True,
    show_errors=True,
) -> list[str]:
    """
    Make a list of words in CST texts from a list of books.
    - Use when keeping the order *is* important.
    - Optionally change the niggahita character (niggahita="ṁ").
    - Optionally dedupe the list (dedupe=True).
    - Optionally show errors (show_errors=True)
    Usage:
    - word_list = make_cst_text_list(pth, ["kn8"], niggahita="ŋ")
    - word_list = make_cst_text_list(pth, ["kn8", "kn9"], dedupe=False)
    - word_list = make_cst_text_list(pth, ["kn8", "kn9"], add_hyphenated_parts=True)
    """

    cst_texts_list: list[str] = []

    for i in books:
        if cst_texts[i]:
            cst_texts_list += cst_texts[i]

    words_list: list[str] = []

    for book in cst_texts_list:
        with open(pth.cst_txt_dir.joinpath(book), "r", encoding="utf-8") as f:
            words_list.extend(
                _text_to_words(f.read(), niggahita, add_hyphenated_parts, show_errors)
            )

    return _finish_words(words_list, add_hyphenated_parts, dedupe)


def _text_to_words(
    text_string: str, niggahita: str, add_hyphenated_parts: bool, show_errors: bool
) -> list[str]:
    # remove all brackets
    text_string = re.sub(r"\(.+?\)", "", text_string)

    if add_hyphenated_parts:
        # dont remove the hyphen, deal with it later
        text_string = clean_machine(
            text_string,
            niggahita=niggahita,
            remove_hyphen=False,
            show_errors=show_errors,
        )
    else:
        # remove the hyphen immediately
        text_string = clean_machine(
            text_string, niggahita=niggahita, remove_hyphen=True
        )

    return text_string.split()


def _finish_words(
    words_list: list[str], add_hyphenated_parts: bool, dedupe: bool
) -> list[str]:
    if add_hyphenated_parts:
        for index, word in enumerate(words_list):
            if "-" in word:
                # remove the dash and add the clean word back into the list
                words_list[index] = word.replace("-", "")

                # split on dashes and add each split back into the list
                # in the correct order
                hyphenated_words = word.split("-")
                for h_word in hyphenated_words.__reversed__():
                    words_list.insert(index + 1, h_word)

    if dedupe is True:
        exists = []
        reduced_list = []
        for word in words_list:
            if word not in exists:
                exists += [word]
                reduced_list += [word]
        return reduced_list
    else:
        return words_list


# "1. apaṇṇakajātakaṃ", and from story 151 on "151. rājovādajātakaṃ (2-1-1)"
JATAKA_STORY_HEADING = re.compile(r"^(\d+)\. .*jātakaṃ(?:\s*\([^)]*\))?\s*$")


def make_cst_jataka_text_list(
    story_range: range,
    niggahita="ṃ",
    dedupe=True,
    add_hyphenated_parts=True,
    show_errors=True,
) -> list[str]:
    """
    Make a list of words in the CST Jātaka root text (kn14) for the stories in a range.
    - A story starts at its numbered heading and runs to the next heading.
    - The lines before the first heading count with story 1.
    - A story whose heading has another shape counts with the story before it.
    """

    words_list: list[str] = []
    current = 1

    for book in cst_texts["kn14"]:
        kept: list[str] = []
        with open(pth.cst_txt_dir.joinpath(book), "r", encoding="utf-8") as f:
            for line in f.read().splitlines():
                heading = JATAKA_STORY_HEADING.match(line.strip())
                if heading:
                    current = int(heading.group(1))
                if current in story_range:
                    kept.append(line)
        words_list.extend(
            _text_to_words(
                "\n".join(kept), niggahita, add_hyphenated_parts, show_errors
            )
        )

    return _finish_words(words_list, add_hyphenated_parts, dedupe)


def make_sc_text_set(
    pth: ProjectPaths, books: list[str], niggahita="ṃ", add_hyphenated_parts=True
) -> set[str]:
    """Make a list of words in Sutta Central texts from a list of books.
    Optionally change the niggahita character.
    Return a list or a set."""

    pr.green_tmr("making sc text set")

    # make a list of file names of included books
    sc_texts_list: list[str] = []
    for i in books:
        try:
            if sc_texts[i]:
                sc_texts_list += sc_texts[i]
        except KeyError as e:
            pr.red(f"book does not exist: {e}")
            return set()

    words_list: list[str] = []

    for root, __dirs__, files in sorted(os.walk(pth.sc_data_dir)):
        for file in files:
            if file in sc_texts_list:
                with open(os.path.join(root, file), encoding="utf-8") as f:
                    # Sutta Cental texts are json dictionaries
                    sc_text_dict: dict = json.load(f)
                    for __title__, text_string in sc_text_dict.items():
                        if add_hyphenated_parts:
                            # dont remove the hyphen, deal with it later
                            text_string = clean_machine(
                                text_string, niggahita=niggahita, remove_hyphen=False
                            )
                        else:
                            # remove the hyphen immediately
                            text_string = clean_machine(
                                text_string, niggahita=niggahita, remove_hyphen=True
                            )

                        words_list.extend(text_string.split())

    if add_hyphenated_parts:
        words_list = hyphenated_parts_adder(words_list)

    pr.yes(len(set(words_list)))
    return set(words_list)


# def make_bjt_text_set(
#         pth: ProjectPaths,
#         include: list[str]
# ) -> set[str]:

#     """This is not currently used."""

#     pr.green("make bjt text set")
#     bjt_texts_list: list[str] = []
#     for i in include:
#         if bjt_texts[i]:
#             bjt_texts_list += bjt_texts[i]

#     bjt_text_string = ""

#     for bjt_text in bjt_texts_list:
#         with open(pth.bjt_text_path.joinpath(bjt_text), "r") as f:
#             bjt_text_string += f.read()

#     bjt_text_string = clean_machine(bjt_text_string)
#     bjt_text_set = set(bjt_text_string.split())

#     pr.yes(len(bjt_text_set))
#     return bjt_text_set


def make_mula_words_set(pth: ProjectPaths) -> set[str]:
    """Returns a set of all words in CST & Sutta Cental mūla texts.
    Usage: mula_word_set = make_mula_words_set()"""

    cst_word_set = make_cst_text_set(pth, mula_books)
    sc_word_set = make_sc_text_set(pth, mula_books)
    mula_word_set = cst_word_set | sc_word_set
    return mula_word_set


def make_all_words_set(pth: ProjectPaths) -> set[str]:
    """Returns a set of all words in CST & Sutta Cental texts.
    Usage: all_words_set = make_all_words_set()"""

    cst_word_set = make_cst_text_set(pth, all_books)
    sc_word_set = make_sc_text_set(pth, all_books)
    all_words_set = cst_word_set | sc_word_set
    return all_words_set


if __name__ == "__main__":
    pth = ProjectPaths()
    # TODO why does it need a path!?

    cst_test_set = make_cst_text_list(["mna"], dedupe=False, add_hyphenated_parts=True)
    print(type(cst_test_set))
    print(len(cst_test_set))
    print(cst_test_set[:10])

    from collections import Counter

    c = Counter(cst_test_set)
    most_common = c.most_common(100)
    print(most_common)
