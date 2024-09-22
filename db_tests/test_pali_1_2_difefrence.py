#!/usr/bin/env python3

"""Test to see if lemma_1 and lemma_2 are almost identical"""

import difflib
import pyperclip
import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths
from tools.pos import INDECLINABLES

error_list = []

exceptions = [
    "eyya 2.1", "tha", "ma 3.1", "sa 4.1",
    "ssa 2", "tara 3", "tara 3",
    "sat 1", "sat 2"]

pos_differs = [
    "masc", "nt", "prefix", "card", "cs",
    "letter", "root", "suffix", "ve"]


def main():
    print("[bright_yellow]find differences in lemma_1, lemma_2, stem pattern")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    error_list = []
    for i in db:
        
        error_list = test_zero(i, error_list)
        error_list = test_one(i, error_list)
        error_list = test_two(i, error_list)
        error_list = test_three(i, error_list)
        error_list = test_stem_pattern(i, error_list)

    error_string = db_search_string(error_list)
    print(error_string)
    pyperclip.copy(error_string)

def test_zero(i, error_list):
    if (
        i.lemma_1 not in exceptions
        and i.pos not in pos_differs
        and i.meaning_1
        and not i.lemma_clean.endswith("ar")
    ):
        diff = 0
        is_same = compare_strings(i.lemma_clean, i.lemma_2, diff)
        if not is_same:
            printer(i)
            error_list += [i.lemma_1]
    return error_list


def test_one(i, error_list):
    if (
        i.lemma_1 not in exceptions
        and not i.lemma_clean.endswith("ant")
        and not i.lemma_clean.endswith("ar")
        and not i.lemma_clean.endswith("as")
    ):  
        diff = 1
        is_same = compare_strings(i.lemma_clean, i.lemma_2, diff)
        if not is_same:
            printer(i)
            error_list += [i.lemma_1]
    return error_list


def test_two(i, error_list):
    if (
        i.lemma_clean.endswith("ar")
        or i.lemma_clean.endswith("as")
    ):
        diff = 2
        is_same = compare_strings(i.lemma_clean, i.lemma_2, diff)
        if not is_same:
            printer(i)
            error_list += [i.lemma_1]
    return error_list

def test_three(i, error_list):
    if (
        i.lemma_clean.endswith("ant")
    ):
        diff = 3
        is_same = compare_strings(i.lemma_clean, i.lemma_2, diff)
        if not is_same:
            printer(i)
            error_list += [i.lemma_1]
    return error_list

def test_stem_pattern(i, error_list):
    if (
        "*" not in i.stem
        and "!" not in i.stem
        and "-" not in i.stem
        and i.pos not in INDECLINABLES
        and " pl" not in i.pattern
    ):
        pattern = re.sub(" .*$", "", i.pattern)
        pattern = re.sub(" .*$", "", i.pattern)
        pattern = pattern.replace("aī", "a")
        pattern = re.sub(r"\d$", "", pattern)
        stem_pattern = f"{i.stem}{pattern}"
        diff = 0
        is_same = compare_strings(i.lemma_clean, stem_pattern, diff)
        if not is_same:
            printer(i)
            error_list += [i.lemma_1]
    return error_list


def printer(i):
    print(f"{i.id:<10}{i.lemma_1:<30}{i.lemma_2:<30}")



def compare_strings(str1: str, str2: str, diff: int):
   # Create a SequenceMatcher object
   sm = difflib.SequenceMatcher(None, str1, str2)
   matching_chars = sm.ratio() * len(str1)
   if len(str1) - matching_chars <= diff:
       return True
   else:
       return False


if __name__ == "__main__":
    main()
