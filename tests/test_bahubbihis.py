#!/usr/bin/env python3

"""
# Bahubbīhi compounds are characterised by 
# - a noun in the last place of the compound
# - pos can be a noun or adjective
# - often contains 'who', 'whose', 'which' in the meaning.
"""

import json
import re
import pyperclip

from rich import print
from typing import Optional

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.meaning_construction import clean_construction, make_meaning
from tools.paths import ProjectPaths
from tools.pali_alphabet import pali_alphabet
from tools.tic_toc import tic, toc
from tools.db_search_string import db_search_string
from tools.terminal_highlights import terminal_bold

class ProgData:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(PaliWord).all()

        self.yes_no: str = "[white]y[green]es [white]n[green]o"
        self.yes_no_maybe: str = "[white]y[green]es [white]n[green]o [white]m[green]aybe"


        self.noun = ["masc", "fem", "nt"]
        self.noun_or_adjective = ["masc", "fem", "nt", "adj"]
        self.relative_pronouns = ["who", "whose", "which"]
        self.nouns_set: set

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


g = ProgData()


def main():
    tic()
    print("[bright_yellow]find bahubbihi compounds")
    make_set_of_all_nouns_list()
    find_bahubbihis()
    toc()


def make_set_of_all_nouns_list():
    """Find all the nouns and put them in a set."""
    print(f"[green]{'making a set of all nouns':<30}", end="")

    nouns_set = set()

    for i in g.db:
        if i.pos in g.noun:
            nouns_set.add(i.pali_clean)

    g.nouns_set = nouns_set

    print(len(nouns_set))


def find_bahubbihis():
    """Find possible bahubbīhi compounds."""
    print(f"[green]{'finding bahubbīhi compounds':<40}")

    for i in g.db:
        if (
            i.meaning_1
            and i.example_1
            and i.pos == "adj"
            and re.findall("\\bcomp\\b", i.grammar)
            and "bahubbīhi" not in i.compound_type
            and i.id not in g.bahubbihi_dict["no"]
             and i.id not in g.bahubbihi_dict["maybe"]
        ):
            # check if the last word of the construction is a noun
            constr = clean_construction(i.construction)
            constr_list = constr.split(" + ")

            # FIXME what about pos is noun?
            # FIXME what about plurals ending in ' + ā' etc?
            # FIXME what about noun in the first position, pp in the second eg. aggappatta
            # FIXME what about noun in the first position, adj in the second, eg paññānirodhika 

            if constr_list[-1] in g.nouns_set:
                # check if there is a relative prounoun
                for rel_pr in g.relative_pronouns:
                    if re.findall(f"\\b{rel_pr}\\b", i.meaning_1):
                        print_check_assign(i, constr)


def print_check_assign(i: PaliWord, constr: str):
    print()
    print(f"- [white]{i.pali_1}")
    print(f"- [green]{i.pos}")
    print(f"- [light_green]{constr}")
    print(
        f"- [green]{i.compound_type} ({terminal_bold(i.compound_construction, 'light_green')})")
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
        pyperclip.copy(i.pali_1)
        print("committed to db")
    
    if route == "n":
        g.update_no(i.id)
        print("saved to 'no'")

    if route == "m":
        g.update_maybe(i.id)
        print("saved to 'maybe'")


if __name__ == "__main__":
    main()


