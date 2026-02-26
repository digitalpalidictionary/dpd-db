#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Find possible bahubbīhi compounds.

Bahubbīhi compounds are characterised by:
- a noun in the last place of the compound
- pos can be a noun or adjective
- often contains 'who', 'whose', 'which' in the meaning
- adj with prefix sa- in the sense of "with"
- adj which has taddhita "ka|ika|aka"
"""

import json
import re

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.terminal_highlights import terminal_bold


class GlobalVars:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()

        self.yes_no: str = "[white]y[green]es [white]n[green]o"
        self.yes_no_maybe: str = (
            "[white]y[green]es [white]n[green]o [white]m[green]aybe [white]q[green]uit"
        )

        self.noun = ["masc", "fem", "nt"]
        self.noun_or_adjective = ["masc", "fem", "nt", "adj"]
        self.relative_pronouns = ["who", "whose", "which"]
        self.nouns_set: set
        self.pure_nouns_set: set
        self.pp_set: set
        self.adjectives_set: set

        self.bahubbihi_dict: dict[str, list[int]] = self.load_bahubbhihi_dict()

    def load_bahubbhihi_dict(self):
        if self.pth.bahubbihi_dict_path.exists():
            with open(self.pth.bahubbihi_dict_path, "r") as f:
                bahubbihi_dict = json.load(f)
                print("[green]loaded bahubbihi_dict json")
        else:
            bahubbihi_dict = {"yes": [], "no": [], "maybe": []}
            print("[green]created a brand new bahubbihi_dict")
        return bahubbihi_dict

    def save_bahubbhihi_dict(self):
        with open(self.pth.bahubbihi_dict_path, "w") as f:
            json.dump(g.bahubbihi_dict, f, indent=4)

    def update_yes(self, id):
        self.bahubbihi_dict["yes"].append(id)
        self.save_bahubbhihi_dict()

    def update_no(self, id):
        self.bahubbihi_dict["no"].append(id)
        self.save_bahubbhihi_dict()

    def update_maybe(self, id):
        self.bahubbihi_dict["maybe"].append(id)
        self.save_bahubbhihi_dict()


g = GlobalVars()


def main():
    pr.tic()
    print("[bright_yellow]find bahubbihi compounds")
    make_sets()
    find_bahubbihis()
    pr.toc()


def make_sets():
    """Build sets of nouns, pure nouns, adjectives, pp, and agent words."""
    print(f"[green]{'making noun/adj sets':<30}", end="")

    nouns_set = set()
    adjectives_set = set()
    pp_set = set()
    agent_set = set()

    for i in g.db:
        if i.pos in g.noun:
            nouns_set.add(i.lemma_clean)
        if i.pos == "adj":
            adjectives_set.add(i.lemma_clean)
        if i.pos == "pp":
            pp_set.add(i.lemma_clean)
        if "agent" in i.grammar:
            agent_set.add(i.lemma_clean)

    g.nouns_set = nouns_set - agent_set
    g.adjectives_set = adjectives_set
    g.pp_set = pp_set
    g.pure_nouns_set = nouns_set - adjectives_set - pp_set - agent_set

    print(f"nouns: {len(g.nouns_set)}, pure_nouns: {len(g.pure_nouns_set)}")


def find_bahubbihis():
    """Find possible bahubbīhi compounds."""
    print(f"[green]{'finding bahubbīhi compounds':<40}")

    total_matches = 0

    for i in g.db:

        # skip if already reviewed
        if i.id in g.bahubbihi_dict["no"]:
            continue
        if i.id in g.bahubbihi_dict["maybe"]:
            continue

        # skip if already tagged as bahubbīhi
        if "bahubbīhi" in i.compound_type:
            continue

        # skip if no meaning
        if not i.meaning_1:
            continue

        #! adjective compound where the last element is a noun
        #! and the meaning contains a relative pronoun
        if (
            i.pos == "adj"
            and re.findall(r"\bcomp\b", i.grammar)
        ):
            constr_list = i.construction_clean.split(" + ")
            last_element = constr_list[-1]

            if last_element in g.nouns_set:
                for rel_pr in g.relative_pronouns:
                    if re.findall(rf"\b{rel_pr}\b", i.meaning_1):
                        total_matches += 1
                        print_check_assign(i, i.construction_clean)
                        break  # avoid duplicates if multiple pronouns match

        #! adjective compound with prefix "sa" (with...) — often bahubbīhi
        #! even without a relative pronoun in the meaning
        elif (
            i.example_1
            and i.pos == "adj"
            and re.findall(r"\bcomp\b", i.grammar)
            and i.construction.startswith("sa +")
        ):
            total_matches += 1
            print_check_assign(i, i.construction_clean)

    print(f"[green]Total matches found: {total_matches}")


def print_check_assign(i: DpdHeadword, constr: str):
    pyperclip.copy(i.lemma_1)  # copy headword immediately for reference

    print()
    print(f"- [white]{i.lemma_1}")
    print(f"- [green]{i.pos}")
    print(f"- [light_green]{constr}")
    print(
        f"- [green]{i.compound_type} ({terminal_bold(i.compound_construction, 'light_green')})"
    )
    print(f"- [cyan]{i.meaning_1}")
    if i.example_1:
        print(f"- [green]{terminal_bold(i.example_1, 'cyan')}")
    if i.example_2:
        print(f"- [light_green]{terminal_bold(i.example_2, 'cyan')}")
    print()

    print(f"[green]is this a bahubbīhi? {g.yes_no_maybe}", end=" ")
    route = input()

    if route == "y":
        i.compound_type += " > bahubbīhi"
        g.db_session.commit()
        g.update_yes(i.id)
        print("committed to db")

    elif route == "n":
        g.update_no(i.id)
        print("saved to 'no'")

    elif route == "m":
        g.update_maybe(i.id)
        print("saved to 'maybe'")

    elif route == "q":
        raise SystemExit


if __name__ == "__main__":
    main()
