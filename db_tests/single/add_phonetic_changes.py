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
from tools.phonetic_change_manager import PhoneticChangeManager, PhoneticChangeResult


def add_update_phonetic(
    db_session, db: list[DpdHeadword], manager: PhoneticChangeManager
) -> bool:
    """Process all headwords and apply phonetic changes based on TSV rules.

    Returns:
        True if user requested a rerun, False otherwise.
    """
    for rule in manager.get_rules():
        if rule["initial"] == "-":
            break

        all_matches: list[tuple[DpdHeadword, PhoneticChangeResult]] = []

        for headword in db:
            result = manager.check_headword_against_rule(headword, rule)
            if result:
                all_matches.append((headword, result))

        if not all_matches:
            print(f"[dim]{rule['line']} {rule['initial']}")
            continue

        print("-" * 40)
        print(f"[green]{'line':<15}: [white]{rule['line']}")
        for k, v in rule.items():
            if k == "line":
                continue
            if k in ("exceptions", "without", "wrong"):
                v = ", ".join(v) if v else "x"
            print(f"[green]{str(k):<15}: [white]{str(v)}")
        print()

        by_status: dict[str, list[str]] = {
            "auto_update": [],
            "auto_add": [],
            "manual_check": [],
        }
        for hw, res in all_matches:
            by_status[res.status].append(hw.lemma_1)
        for status, lemmas in by_status.items():
            print(f"[green]{status:<15}: [white]{db_search_string(lemmas)}")

        committable = [
            (hw, res)
            for hw, res in all_matches
            if res.status in ("auto_add", "auto_update")
        ]
        manual_checks = [
            (hw, res) for hw, res in all_matches if res.status == "manual_check"
        ]

        # auto_add + auto_update: batch flow with optional exceptions
        while committable:
            committable_names = ", ".join(hw.lemma_1 for hw, _ in committable)
            print(f"\n[green]commit ({len(committable)}): [white]{committable_names}")

            choice = Prompt.ask(
                "[yellow](c)ommit all, (e)xceptions, (r)erun, e(x)it, any key to pass"
            )

            if choice == "x":
                db_session.close()
                return False
            elif choice == "r":
                db_session.close()
                return True
            elif choice == "e":
                exceptions_input = Prompt.ask(
                    "[yellow]Enter exceptions (comma separated)"
                )
                exception_lemmas = [
                    e.strip() for e in exceptions_input.split(",") if e.strip()
                ]
                for lemma in exception_lemmas:
                    manager.add_exception(rule, lemma)
                    print(f"[green]{lemma} added as exception")
                committable = [
                    (hw, res)
                    for hw, res in committable
                    if hw.lemma_1 not in exception_lemmas
                ]
            elif choice == "c":
                for hw, res in committable:
                    if res.status == "auto_add":
                        hw.phonetic = str(rule["correct"])
                    elif res.status == "auto_update":
                        lines = hw.phonetic.split("\n")
                        new_lines = [
                            str(rule["correct"]) if line in rule["wrong"] else line
                            for line in lines
                        ]
                        hw.phonetic = "\n".join(new_lines)
                db_session.commit()
                print(f"[green]{len(committable)} words committed")
                break
            else:
                break

        # manual_check: display, add exceptions, pause
        while manual_checks:
            manual_names = db_search_string([hw.lemma_1 for hw, _ in manual_checks])
            print(f"\n[green]manual_check:   [white]{manual_names}")
            pyperclip.copy(manual_names)
            choice = Prompt.ask(
                "[yellow](e)xceptions, (r)erun, e(x)it, any key to continue"
            )
            if choice == "x":
                db_session.close()
                return False
            elif choice == "r":
                db_session.close()
                return True
            elif choice == "e":
                exceptions_input = Prompt.ask(
                    "[yellow]Enter exceptions (comma separated)"
                )
                exception_lemmas = [
                    e.strip() for e in exceptions_input.split(",") if e.strip()
                ]
                for lemma in exception_lemmas:
                    manager.add_exception(rule, lemma)
                    print(f"[green]{lemma} added as exception")
                manual_checks = [
                    (hw, res)
                    for hw, res in manual_checks
                    if hw.lemma_1 not in exception_lemmas
                ]
            else:
                break

    db_session.close()
    return False


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

    while True:
        manager = PhoneticChangeManager(pth.phonetic_changes_path)
        db_session = get_db_session(pth.dpd_db_path)
        db_session.expire_on_commit = False
        db = db_session.query(DpdHeadword).filter(DpdHeadword.meaning_1 != "").all()

        list_all_phonetic_changes(db, manager)
        rerun = add_update_phonetic(db_session, db, manager)
        if not rerun:
            break
        print("\n[yellow]Rerunning with fresh data...\n")
    # finder(db, manager, "ṃs > s")

# FIXME test for xyz not in pali
# FIXME test for xyz not in base
# FIXME test for xyz not in construction
# FIXME exceptions must be a list
# FIXME without must be a list
