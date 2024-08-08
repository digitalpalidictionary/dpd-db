#!/usr/bin/env python3

"""Find words in commentary columns which
1. don't exist in the dictionary
2. need meaning
3. needs example
"""
import re
import pyperclip

from rich import print

from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup
from tools.paths import ProjectPaths
from tools.goldendict_tools import open_in_goldendict_os
from tools.clean_machine import clean_machine

pth = ProjectPaths()
db_session = get_db_session(pth.dpd_db_path)


def make_clean_commentary_list(i: DpdHeadwords) -> list:
    """Clean up the commentary and return a list of words."""
    
    clean_commentary = re.sub("\(.*?\)", "", i.commentary)      # remove word in brackets
    clean_commentary = clean_commentary.replace("<b>", "")      # remove bold tags
    clean_commentary = clean_commentary.replace("</b>", "")     
    clean_commentary = clean_machine(clean_commentary)          # remove punctuation
    return clean_commentary.split()


def check_in_lookup(word: str):
    lookup = db_session.query(Lookup) \
        .filter_by(lookup_key=word) \
        .first()
    if lookup:
        return True, lookup
    else:
        return False, None


def check_word(i: DpdHeadwords, word: str):
    """
    Check if a word 
    1. exists in the lookup table."""

    in_lookup, lookup = check_in_lookup(word)
    if not in_lookup:
        print_word_does_not_exist(i, word)


def print_word_does_not_exist(i: DpdHeadwords, word: str):
    print(f"[cyan]{i.id}. {i.lemma_1}")
    print(f"[green]{i.commentary}")
    print(word)
    pyperclip.copy(word)
    input()


def main():

    db = db_session.query(DpdHeadwords) \
        .filter(DpdHeadwords.commentary!="") \
        .all()

    for i in db:
        clean_commentary_list = make_clean_commentary_list(i)
        for word in clean_commentary_list:
            check_word(i, word)


if __name__ == "__main__":
    main()
