#!/usr/bin/env python3

"""Find words in example_1, example_2 and commentary columns which
1. don't exist in the dictionary
2. need meaning
3. needs example
"""

import re
import pyperclip

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths
from tools.goldendict_tools import open_in_goldendict_os
from tools.clean_machine import clean_machine

# 3 Routes
# 1: find missing headwords
# 2: find missing meaning_1
# 3: find missing examples

class GlobalData():
    route: int = 3 
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    lookup: Lookup
    i: DpdHeadword
    word: str
    column: str
    text: str


def refresh_db_session(g: GlobalData):
    """Keep the db up to date with changes"""
    g.db_session = get_db_session(g.pth.dpd_db_path)


def make_clean_word_list(g: GlobalData) -> list:
    """Clean up the text in the column and return a list of words."""
    g.text = getattr(g.i, g.column)  
    g.text = re.sub("\(.*?\)", "", g.text)      # remove word in brackets
    g.text = g.text.replace("<b>", "")          # remove bold tags
    g.text = g.text.replace("</b>", "")     
    g.text = clean_machine(g.text)
    g.text = g.text.replace("-", " ")           # remove punctuation
    return g.text.split()


def check_in_lookup(g: GlobalData):
    g.lookup = g.db_session.query(Lookup) \
        .filter_by(lookup_key=g.word) \
        .first()


def print_results(g: GlobalData):
    print(f"[cyan]{g.i.id}")
    print(f"[cyan]{g.i.lemma_1}")
    print(f"[cyan]{g.column}")
    if g.column == "example_1":
        print(g.i.source_1, g.i.sutta_1)
    elif g.column == "example_2":
        print(g.i.source_2, g.i.sutta_2)
    text_highlight = g.text.replace(g.word, f"[cyan]{g.word}[/cyan]")
    print(f"[green]{text_highlight}")
    print(f"[cyan]{g.word}")
    pyperclip.copy(g.word)
    input()



def find_missing_meaning_1(g: GlobalData):
    """Check if any word in the lookup is missing a meaning_1."""

    needs_meaning_1 = True
    dpd_ids = g.lookup.headwords_unpack
    if dpd_ids:
        for dpd_id in dpd_ids:
            headword = g.db_session.query(DpdHeadword).filter_by(id=dpd_id).first()
            if headword.meaning_1:
                needs_meaning_1 = False
        if needs_meaning_1:
            print_results(g)


def find_missing_eg(g: GlobalData):
    """Check if any word in the lookup is missing an eg"""
    
    needs_eg = True
    dpd_ids = g.lookup.headwords_unpack
    if dpd_ids:
        for dpd_id in dpd_ids:
            headword = g.db_session.query(DpdHeadword).filter_by(id=dpd_id).first()
            if headword.meaning_1 and headword.example_1:
                needs_eg = False
        if needs_eg:
                print_results(g)


def check_word(g: GlobalData):
    """
    Check if a word 
    1. exists in the lookup table.
    2. (check if word has meaning_1)
    3. (check if word has example_1)
    """

    check_in_lookup(g)
    if not g.lookup:
        if g.route == 1:
            print_results(g)
    else:
        if g.route == 2:
            find_missing_meaning_1(g)
        elif g.route == 3:
            find_missing_eg(g)


def main():
    g = GlobalData()
    for g.i in g.db:
        refresh_db_session(g)
        for g.column in ["example_1", "example_2"]: #, "commentary"]:  
            clean_word_list = make_clean_word_list(g)
            for g.word in clean_word_list:
                check_word(g)


if __name__ == "__main__":
    main()


