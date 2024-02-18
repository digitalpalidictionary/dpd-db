#!/usr/bin/env python3

"""Test the bold word in examples is an actual inflection of the headword."""

import re
import pyperclip
from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from sqlalchemy.orm import joinedload
from tools.configger import config_test



def check_username():
    if config_test("user", "username", "deva"):
        return True
    else:
        return False


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dps_data: bool = check_username()
    if dps_data:
        db = db_session.query(DpdHeadwords).options(joinedload(DpdHeadwords.sbs)).all()
    else:
        db = db_session.query(DpdHeadwords).all()
    pali_alphabet: list[str] = pali_alphabet
    i: DpdHeadwords
    if dps_data:
        fields: list[str] = ["sbs_example_1", "sbs_example_2", "sbs_example_3", "sbs_example_4"]
    else:
        fields: list[str] = ["example_1", "example_2"]
    field: str
    bold_words: list[str]
    bold_word: str
    inflections_list: list[str]
    clean_bold_word: str
    counter: int = 1



def main():
    g = ProgData
    for i in g.db:
        g.i = i
        if i.pos not in ["idiom"]:
            # search in a list of fields
            for field in g.fields:
                g.field = field
                if g.dps_data:
                    find_all_bold_words_sbs(g)
                else:
                    find_all_bold_words(g)
                get_inflections(g)
                for bold_word in g.bold_words:
                    g.bold_word = bold_word
                    test1(g)


def find_all_bold_words(g):
    """Get All the bold words from the string."""
    g.bold_words = re.findall("<b>.+?<\\/b>", getattr(g.i, g.field))


def find_all_bold_words_sbs(g):
    """Get All the bold words from the string."""
    if g.i.sbs is not None:
        g.bold_words = re.findall("<b>.+?<\\/b>", getattr(g.i.sbs, g.field))
    else:
        g.bold_words = []


def get_inflections(g):
    """Get the inflections list."""
    g.inflections_list = g.i.inflections_list


def test1(g):
    """Clean up the word from tags and internal punctuation.
    Test if there's something left"""
    g.clean_bold_word = g.bold_word\
        .replace("<b>", "")\
        .replace("</b>", "")\
        .replace("'", "")\
        .replace("-", "")\
        .strip()
    if not g.clean_bold_word:
        printer(g, "test1")
        return
    else:
        test2(g)


def test2(g):
    """test 2, non-pali characters in the word."""
    for char in g.clean_bold_word:
        if char not in g.pali_alphabet:
            printer(g, "test2")
            return
    test3(g)


def test3(g):
    """test 3, clean bold is in inflections list."""
    if g.clean_bold_word in g.inflections_list:
        return
    else:
        test4(g)


def test4(g):
    """"test 4, missing last letter is the problem."""
    for inflection in g.inflections_list:
        if re.findall(f"{g.clean_bold_word}.", inflection):
            return
    test5(g)


def test5(g):
    """test 5, nasals in last position."""
    nasals = ["ṅ", "ñ", "ṇ", "n", "m"]
    if g.clean_bold_word[-1] in nasals:
        clean_bold_nasal = f"{g.clean_bold_word[:-1]}ṃ"
        if clean_bold_nasal in g.inflections_list:
            return
        else:
            test6(g)


def test6(g):
    """test 6, ññ in last position."""
    if g.clean_bold_word[-2:] == "ññ":
        clean_bold_nasal = f"{g.clean_bold_word[:-2]}ṃ"
        if clean_bold_nasal in g.inflections_list:
            return
    printer(g, "test6")


def printer(g, message):
    """Print out the problem and up the tally."""
    p = f"{g.counter:<4}{g.i.id:<8}{g.i.lemma_1:<40}"
    p += f"[deep_sky_blue4]{g.field:<10}"
    p += f"[chartreuse2]{g.clean_bold_word:<30}"
    p += f"[light_sky_blue3]{message:<10}"
    print(p, end="")
    g.counter += 1
    pyperclip.copy(g.i.lemma_1)
    # input("press enter to continue: ")
    print()
    

if __name__ == "__main__":
    main()
