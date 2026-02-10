#!/usr/bin/env python3

"""
Search for missing or wrong compound types according to TSV criteria.
"""

import re

import pyperclip
from rich import print
from rich.prompt import Prompt

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.compound_type_manager import CompoundTypeManager
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()

    # Use CompoundTypeManager for detection logic
    manager = CompoundTypeManager(pth.compound_type_path)
    rules = manager.get_rules()

    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    for c_counter, rule in enumerate(rules):
        print("-" * 40)
        for k, v in rule.items():
            print(f"[green]{str(k):<15}: [cyan]{str(v if v else '[red]None')}")
        print()

        pos_list = (
            rule["pos"].split(", ")
            if isinstance(rule["pos"], str) and rule["pos"] != "any"
            else []
        )
        search_list: list = []
        i_counter = 0

        for i in db:
            # Use manager's optimized single-rule check
            detected_type = manager.check_headword_against_rule(
                rule=rule,
                construction=i.construction,
                pos=i.pos,
                grammar=i.grammar,
                lemma=i.lemma_1,
                meaning_1=i.meaning_1,
                compound_type=i.compound_type,
            )

            if detected_type is None:
                continue

            # Additional POS check if rule specifies non-any
            if rule["pos"] != "any" and i.pos not in pos_list:
                continue

            search_list += [i.lemma_1]
            i_counter += 1
            pyperclip.copy(i.lemma_1)
            printer(i)
            input()

        if search_list:
            print(i_counter)
            search_string = db_search_string(search_list)
            print(f"\n{search_string}")
            pyperclip.copy(search_string)
            if c_counter < len(rules) - 1:
                user_input = Prompt.ask("[yellow]Press ENTER to continue or X to exit")
                if user_input == "x":
                    break


def printer(i: DpdHeadword) -> None:
    string = ""
    string += f"[white]{i.lemma_1[:29]:<30}"
    string += f"[cyan]{i.pos:<10}"
    string += f"[white]{i.meaning_combo[:49]:<50}"
    construction = re.sub("\n.+", "", i.construction)
    string += f"[cyan]{construction[:29]:<30}"
    string += f"[white]{i.compound_type[:14]:<15}"
    string += f"[cyan]{i.compound_construction[:19]:}"
    print(string)


if __name__ == "__main__":
    main()
