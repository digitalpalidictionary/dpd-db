#!/usr/bin/env python3

"""Tets that family compounds have meaning_1 and headword."""

import pyperclip
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, FamilyCompound
from tools.paths import ProjectPaths


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_fc = db_session.query(FamilyCompound).all()
    db_hw = db_session.query(PaliWord).all()
    family_compound_set: set[str] = set()
    no_meaning_dict: dict[str, dict[str, str]]
    no_pali_1: set[str] = set()


def main():
    print("[bright_yellow]find family compounds with no meaning_1, pali_1")
    g = ProgData()
    make_family_compound_set(g)
    test_family_compounds_have_meaning_1(g)
    display_missing_meanings(g)


def make_family_compound_set(g):
    """Make a set of all the family compounds"""
    for i in g.db_fc:
        g.family_compound_set.add(i.compound_family)


def test_family_compounds_have_meaning_1(g):
    """Test that the family compounds have meaning_1."""
    
    no_meaning_dict = {}
    for i in g.db_hw:
        if i.pali_clean in g.family_compound_set:
            if i.meaning_1:

                if no_meaning_dict.get(i.pali_clean):
                    no_meaning_dict[i.pali_clean]["yes"].append(i.pali_1)
                else:
                    no_meaning_dict[i.pali_clean] = {"yes": [i.pali_1], "no": []}
            
            else:
                if no_meaning_dict.get(i.pali_clean):
                    no_meaning_dict[i.pali_clean]["no"].append(i.pali_1)
                else:
                    no_meaning_dict[i.pali_clean] = {"yes": [], "no": [i.pali_1]}
    
    g.no_meaning_dict = no_meaning_dict


def display_missing_meanings(g):
    """Display the missing meanings for processing."""

    total = 0
    for pali_clean, data in g.no_meaning_dict.items():
        if not data["yes"]:
            total += 1 

    count = 0
    for pali_clean, data in g.no_meaning_dict.items():

        if not data["yes"]:
            print(f"[green]{count+1} of {total+1}")
            print(f"[green]{'pali_clean':20}[red]{pali_clean}")
            print(f"[green]{'in headwords':<20}[white]{' '.join(data['no'])}")
            pyperclip.copy(pali_clean)
            input("press enter to continue: ")
            print()
            count += 1

if __name__ == "__main__":
    main()
