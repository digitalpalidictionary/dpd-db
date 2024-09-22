#!/usr/bin/env python3

"""
Search for missing or wrong vowel sandhi according to TSV criteria.
"""

import pyperclip
import re

from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths
from tools.printer import p_title
from tools.tsv_read_write import read_tsv_dot_dict
from tools.pali_sort_key import pali_list_sorter


def compile_previous_next(c, construction_clean, base_clean):
    
    """Compile strings of previous + initial + next letters in
    construction and base."""

    try:
        c_prev = re.findall(f".{c.initial}", construction_clean)[0]
        c_prev = c_prev.replace(c.initial, "")
    except Exception:
        c_prev = "x"
    try:
        c_next = re.findall(f"{c.initial}.", construction_clean)[0]
        c_next = c_next.replace(c.initial, "")
    except Exception:
        c_next = "x"
    
    c_compiled = f"{c_prev}{c.final}{c_next}"
    
    try:
        b_prev = re.findall(f".{c.initial}", base_clean)[0]
        b_prev = b_prev.replace(c.initial, "")
    except Exception:
        b_prev = "x"
    try:
        b_next = re.findall(f"{c.initial}.", base_clean)[0]
        b_next = b_next.replace(c.initial, "")
    except Exception:
        b_next = "x"
    
    b_compiled = f"{b_prev}{c.final}{b_next}"

    return c_compiled, b_compiled


def clean_construction_base(i: DpdHeadword) -> tuple[str, str]:
    
    """Construction and base with
    1. no lines2
    2. no phonetic changes
    3. no root symbol
    """
    construction_clean = re.sub("√", "", i.construction_clean)
    construction_clean = re.sub(r"\*", "", construction_clean)
    construction_clean = re.sub(r" \+ ", " ", construction_clean)
    
    base_clean = re.sub("√", "", i.root_base_clean)
    base_clean = re.sub(r"\*", "", base_clean)
    base_clean = re.sub(r" \+ ", " ", base_clean)
    
    return construction_clean, base_clean


def add_update_phonetic(db_session, db, csv):
    
    for c_counter, c in enumerate(csv):
        if c.initial == "-":
            break

        print("-"*40)
        for k, v in c.items():
            print(f"[green]{str(k):<15}: [white]{str(v)}")
        print()

        auto_updated = []
        auto_added = []
        manual_update = []

        for i_counter, i in enumerate(db):
            i: DpdHeadword

            if (
                i.meaning_1 and
                i.construction and
                i.lemma_1 not in c.exceptions
            ):
                construction_clean, base_clean = clean_construction_base(i)


                # test construction
                if (
                    c.initial in construction_clean
                    or c.initial in base_clean
                ):

                    c_compiled, b_compiled = compile_previous_next(c, construction_clean, base_clean)

                    if (
                        (
                            c_compiled in i.lemma_1
                            or b_compiled in i.lemma_1
                        )
                        and c.correct not in i.phonetic
                        and (
                            c.without not in construction_clean
                            and c.without not in base_clean
                        )
                    ):
                    
                        # auto update wrong to correct
                        if (
                            c.wrong
                            and c.wrong in i.phonetic
                        ):
                            i.phonetic = re.sub(
                                fr"\b{c.wrong}\b", str(c.correct), str(i.phonetic))
                            auto_updated += [i.lemma_1]
                        
                        # if i.phonetic empty > auto add correct
                        elif not i.phonetic:
                            i.phonetic = c.correct
                            auto_added += [i.lemma_1]
                            
                        # if i.phonetic not empty > compile a list to change manually
                        else:
                            manual_update += [i.lemma_1]

        
        print(f"[green]{'auto_updated':<15}: [white]{db_search_string(auto_updated)} [{len(auto_updated)}]")
        print(f"[green]{'auto_added':<15}: [white]{db_search_string(auto_added)} [{len(auto_added)}]")
        
        manual_update_string = db_search_string(manual_update)
        print(f"[green]{'manual_update':<15}: [white]{manual_update_string} [{len(manual_update)}]")
        pyperclip.copy(manual_update_string)

        if (
            (auto_updated or auto_added or manual_update) and
            c_counter < len(csv)-1
        ):
            Prompt.ask("[yellow]Press any key to continue")

    print(f"{'-'*40}\n")
    commitment = Prompt.ask("[yellow]Press 'c' to commit")
    if commitment == "c":
        # db_session.commit()
        print("[red]Changes committed to db")
    else:
        print("[red]Changes not committed to db")

    db_session.close()


def finder(db, csv, string):
    found = []

    for i in db:
        for p in i.phonetic.split("\n"):
            if string == p:
                found += [i.lemma_1]
    
    if found:
        found_string = db_search_string(found)
        print(f"[cyan]{string}")
        print(f"[white]{found_string}")
        pyperclip.copy(found_string)
    else:
        print(None)


def main():
    p_title("find phonetic changes in vowels")
    pth = ProjectPaths()
    csv = read_tsv_dot_dict(pth.phonetic_changes_vowels_path)
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    add_update_phonetic(db_session, db, csv)


if __name__ == "__main__":
    main()
