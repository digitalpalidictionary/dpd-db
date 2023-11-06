#!/usr/bin/env python3

"""
Search for missing or wrong phonetic changes according to TSV criteria.
"""

import pyperclip
import re

from rich import print
from rich.prompt import Prompt

from db.get_db_session import get_db_session
from db.models import PaliWord

from tools.db_search_string import db_search_string
from tools.meaning_construction import (
    make_meaning, clean_construction)
from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict


def main():
    pth = ProjectPaths()
    csv = read_tsv_dot_dict(pth.phonetic_changes_path)

    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    pos_exclusions = ["sandhi", "idiom"]
    
    for c_counter, c in enumerate(csv):
        if c.initial == "-":
            break

        print("-"*40)
        for k, v in c.items():
            print(f"[green]{str(k):<15}: [white]{str(v)}")
        print()
        # exceptions = c.exceptions.split(", ")
        auto_updated = []
        auto_added = []
        manual_update = []

        for i_counter, i in enumerate(db):

            if (
                i.construction and
                i.meaning_1 and
                i.pali_1 not in c.exceptions):

                # construction and base with:
                # no lines2, ph changes or root symbol
                construction_clean = clean_construction(i.construction)
                construction_clean = re.sub("√", "", construction_clean)
                base_clean = clean_construction(i.root_base)
                base_clean = re.sub("√", "", base_clean)

                # test construction
                if (
                    (
                        c.initial in construction_clean or
                        c.initial in base_clean
                    ) and
                    c.final in i.pali_clean and
                    c.correct not in i.phonetic and
                    (
                        c.without not in construction_clean and
                        c.without not in base_clean
                    )
                ):
                    # auto update wrong to correct
                    if (
                        c.wrong and
                        c.wrong in i.phonetic
                    ):
                        i.phonetic = re.sub(
                            str(c.wrong), str(c.correct), str(i.phonetic))
                        auto_updated += [i.pali_1]
                    
                    # if i.phonetic empty > auto add correct
                    elif not i.phonetic:
                        i.phonetic = c.correct
                        auto_added += [i.pali_1]
                        
                    # if i.phonetic not empty > compila a list to change manually
                    else:
                        manual_update += [i.pali_1]

        
        print(f"[green]{'auto_updated':<15}: [white]{db_search_string(auto_updated)}")
        print(f"[green]{'auto_added':<15}: [white]{db_search_string(auto_added)}")
        
        manual_update_string = db_search_string(manual_update)
        print(f"[green]{'manual_update':<15}: [white]{manual_update_string}")
        pyperclip.copy(manual_update_string)

        if (
            (auto_updated or auto_added or manual_update) and
            c_counter < len(csv)-1
        ):
            Prompt.ask("[yellow]Press any key to continue")

    print(f"{'-'*40}\n")
    commitment = Prompt.ask("[yellow]Press 'c' to commit")
    if commitment == "c":
        db_session.commit()
        print("[red]Changes committed to db")
    else:
        print("[red]Changes not committed to db")

    db_session.close()


def finder():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    found = []

    for i in db:
        if (
            "v > b" in str(i.phonetic) and
            "īv" in str(i.phonetic)
        ):
            found += [i.pali_1]
            i.phonetic = re.sub("v > b\n", "", str(i.phonetic))
            i.phonetic = re.sub("\nv > b", "", str(i.phonetic))
    
    found_string = db_search_string(found)
    print(f"[green]{'found':<15}: [white]{found_string}")
    pyperclip.copy(found_string)

    # db_session.commit()



if __name__ == "__main__":
    main()
    # finder()