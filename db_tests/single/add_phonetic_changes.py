#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Search for missing or wrong phonetic changes according to TSV criteria.
"""

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.phonetic_change_manager import PhoneticChangeManager


def add_update_phonetic(
    db_session, db: list[DpdHeadword], manager: PhoneticChangeManager
):
    """Process all headwords and apply phonetic changes based on TSV rules.

    Args:
        db_session: Database session for committing changes
        db: List of DpdHeadword objects to process
        manager: PhoneticChangeManager instance with loaded rules
    """
    for rule_counter, rule in enumerate(manager.get_rules()):
        if rule["initial"] == "-":
            break

        print("-" * 40)
        for k, v in rule.items():
            if k == "exceptions":
                v = ", ".join(v) if v else "x"
            print(f"[green]{str(k):<15}: [white]{str(v)}")
        print()

        auto_updated = []
        auto_added = []
        manual_update = []

        for headword in db:
            result = manager.check_headword_against_rule(headword, rule)

            if result:
                if result.status == "auto_update":
                    # Replace wrong with correct
                    import re

                    current_phonetic: str = headword.phonetic or ""
                    headword.phonetic = re.sub(
                        f"\\b{rule['wrong']}\\b", str(rule["correct"]), current_phonetic
                    )
                    auto_updated += [headword.lemma_1]

                elif result.status == "auto_add":
                    # Set phonetic to correct
                    headword.phonetic = str(rule["correct"])
                    auto_added += [headword.lemma_1]

                elif result.status == "manual_check":
                    # Compile list for manual review
                    manual_update += [headword.lemma_1]

        print(f"[green]{'auto_updated':<15}: [white]{db_search_string(auto_updated)}")
        print(f"[green]{'auto_added':<15}: [white]{db_search_string(auto_added)}")

        manual_update_string = db_search_string(manual_update)
        print(f"[green]{'manual_update':<15}: [white]{manual_update_string}")
        pyperclip.copy(manual_update_string)

        if (auto_updated or auto_added or manual_update) and rule_counter < len(
            manager.get_rules()
        ) - 1:
            Prompt.ask("[yellow]Press any key to continue")

    # Ask for commitment
    commitment = Prompt.ask("[yellow]Press 'c' to commit")
    if commitment == "c":
        db_session.commit()
        print("[red]Changes committed to db")
    else:
        print("[red]Changes not committed to db")

    db_session.close()


def finder(db, manager: PhoneticChangeManager, string: str):
    """Find headwords with a specific phonetic change.

    Args:
        db: List of DpdHeadword objects to search
        manager: PhoneticChangeManager instance (not used, kept for API compatibility)
        string: The phonetic change string to search for
    """
    found = []

    for headword in db:
        for p in headword.phonetic.split("\n"):
            if string == p:
                found += [headword.lemma_1]

    if found:
        found_string = db_search_string(found)
        print(f"[cyan]{string}")
        print(f"[white]{found_string}")
        pyperclip.copy(found_string)
    else:
        print(None)


def list_all_phonetic_changes(db, manager: PhoneticChangeManager):
    """List all phonetic changes not covered by TSV rules.

    Args:
        db: List of DpdHeadword objects to process
        manager: PhoneticChangeManager instance with loaded rules
    """
    # All phonetic changes minus all correct values from rules
    all_phonetic_set = set()
    correct = set()

    for rule in manager.get_rules():
        if rule["initial"] and rule["initial"] != "-":
            correct.update([rule["correct"]])

    for headword in db:
        if headword.phonetic:
            phonetic = headword.phonetic.split("\n")
            all_phonetic_set.update(phonetic)

    all_phonetic_set = all_phonetic_set.difference(correct)
    all_phonetic_list = pali_list_sorter(list(all_phonetic_set))

    with open("temp/phonetic_changes.txt", "w") as f:
        for p in all_phonetic_list:
            f.write(f"{p}\n")


if __name__ == "__main__":
    pth = ProjectPaths()
    manager = PhoneticChangeManager(pth.phonetic_changes_path)

    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    list_all_phonetic_changes(db, manager)
    add_update_phonetic(db_session, db, manager)
    # finder(db, manager, "ṃs > s")

# FIXME test for xyz not in pali
# FIXME test for xyz not in base
# FIXME test for xyz not in construction
# FIXME exceptions must be a list
# FIXME without must be a list
