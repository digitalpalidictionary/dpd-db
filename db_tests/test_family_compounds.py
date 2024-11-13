#!/usr/bin/env python3

"""Find missing compound families."""

import re
import pickle
import pyperclip

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.tic_toc import tic, toc
from tools.meaning_construction import clean_construction
from tools.paths import ProjectPaths


def make_dict_of_sets(db):
    print("[green]making sets")

    d = {
        "all_words_in_construction": set(),
        "all_words_in_family_compound": set(),
        "all_clean_headwords": set(),
        "all_empty_family_compounds": set(),
        "all_compound_headwords": set()
    }

    for i in db:
        construction = clean_construction(i.construction)

        # all_words_in_construction
        if (
            i.meaning_1 and
            re.findall(r"\bcomp\b", i.grammar) and
            re.findall(r"\+", construction) and
            i.family_compound
        ):
            d["all_words_in_construction"].update(
                construction.split(" + "))

        # all_words_in_family_compound
        if (
            i.meaning_1 and
            i.family_compound
        ):
            d["all_words_in_family_compound"].update(
                i.family_compound_list)

        # all_clean_headwords
        if (i.meaning_1):
            d["all_clean_headwords"].update([i.lemma_clean])
            

        # all_empty_family_compounds
        if (
            i.meaning_1 
            and not i.family_compound
            and not i.meaning_1.startswith("name of")
        ):
            d["all_empty_family_compounds"].update([i.lemma_clean])

        # all_compound_headwords
        if (
            i.meaning_1 and
            re.findall(r"\bcomp\b", i.grammar)
        ):
            d["all_compound_headwords"].update([i.lemma_clean])

    return d


def load_exceptions():
    try:
        with open("family_compound_exceptions") as f:
            exceptions = pickle.load(f)
    except FileNotFoundError:
        exceptions = set()
    return exceptions


def test_family_compound(d):
    # "all_words_in_construction": set(),
    # "all_words_in_family_compound": set(),
    # "all_clean_headwords": set(),
    # "all_empty_family_compounds": set(),
    # "all_compound_headwords": set()

    failures = set()
    for word in d["all_empty_family_compounds"]:
        if (
            word in d["all_words_in_construction"]
            and word not in d["all_words_in_family_compound"]
            and word in d["all_clean_headwords"]
            and word not in d["all_compound_headwords"]
        ):
            failures.update([word])

    return failures


def add_to_db(failures):
    print("[green]adding failures to db")
    exceptions = load_exceptions()
    print(len(failures))

    for counter, failure in enumerate(failures):
        if failure not in exceptions:
            sql_search_term = re.escape(failure)
            sql_query = f"SELECT lemma_1, grammar, meaning_1, family_compound, construction FROM dpd_headwords WHERE (lemma_1 REGEXP '\\b{sql_search_term}\\b' OR construction REGEXP '\\b{sql_search_term}\\b') AND meaning_1 <> ''"
            print(counter+1)
            print(failure, end=" ")
            pyperclip.copy(sql_query)
            input()
            regex_search_term = f"/\\b{failure}\\b/"
            print(regex_search_term, end=" ")
            pyperclip.copy(regex_search_term)
            input()
            print()


def main():
    tic()
    print("[bright_yellow]finding missing family_compounds")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    d: dict = make_dict_of_sets(db)
    failures = test_family_compound(d)
    add_to_db(failures)
    toc()


if __name__ == "__main__":
    main()
