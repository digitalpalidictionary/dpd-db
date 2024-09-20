#!/usr/bin/env python3

"""
# Bahubbīhi compounds are characterised by 
# - a noun in the last place of the compound
# - pos can be a noun or adjective
# - often contains 'who', 'whose', 'which' in the meaning.
# - adj with preffix sa- in the sense of "with"
# - adj which has taddhita "ka|ika|aka"
# Find possible candidates and assign them accordingly. 
"""

import json
import re
import pyperclip
import csv


from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.meaning_construction import clean_construction
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.terminal_highlights import terminal_bold

class ProgData:
    def __init__(self) -> None:
        self.pth = ProjectPaths()
        self.db_session = get_db_session(self.pth.dpd_db_path)
        self.db = self.db_session.query(DpdHeadword).all()

        self.yes_no: str = "[white]y[green]es [white]n[green]o"
        self.yes_no_maybe: str = "[white]y[green]es [white]n[green]o [white]m[green]aybe"

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

    print(len(g.nouns_set), len(g.pure_nouns_set))


def find_bahubbihis():
    """Find possible bahubbīhi compounds."""
    print(f"[green]{'finding bahubbīhi compounds':<40}")

    total_matches =  0
    matching_lemmas = []

    for i in g.db:

        # FIXME what about pos is noun?
        # FIXME what about plurals ending in ' + ā' etc?
        # FIXME what about noun in the first position, pp in the second eg. aggappatta
        # FIXME what about noun in the first position, adj in the second, eg paññānirodhika 
        # FIXME what about using g.nouns_set?

        #! check for adj with relative_pronouns in the meaning which ends on noun
        # if (
        #     i.meaning_1
        #     and i.example_1
        #     and i.pos == "adj"
        #     and re.findall("\\bcomp\\b", i.grammar)
        #     and "bahubbīhi" not in i.compound_type
        #     and i.id not in g.bahubbihi_dict["no"]
        #     and i.id not in g.bahubbihi_dict["maybe"]
        # ):
        #     # check if the last word of the construction is a noun
        #     constr = clean_construction(i.construction)
        #     constr_list = constr.split(" + ")

        #     if constr_list[-1] in g.nouns_set:
                
                
        #         # check if there is a relative prounoun
        #         for rel_pr in g.relative_pronouns:
        #             if re.findall(f"\\b{rel_pr}\\b", i.meaning_1):
        #                 total_matches +=  1
        #                 matching_lemmas.append(i.lemma_1)
        #                 print_check_assign(i, constr)

        #! check for adj with relative_pronouns in the meaning which ends on adj
        # if (
        #     i.meaning_1
        #     and i.example_1
        #     # and any (pos in i.pos for pos in g.noun_or_adjective )
        #     and i.pos == "adj"
        #     and re.findall("\\bcomp\\b", i.grammar)
        #     and "bahubbīhi" not in i.compound_type
        #     and i.id not in g.bahubbihi_dict["no"]
        #     and i.id not in g.bahubbihi_dict["maybe"]
        # ):
        #     # check if the last word of the construction is a noun
        #     constr = clean_construction(i.construction)
        #     constr_list = constr.split(" + ")

        #     if constr_list[-1] in g.adjectives_set:
                
        #         # check if there is a relative prounoun
        #         for rel_pr in g.relative_pronouns:
        #             if re.findall(f"\\b{rel_pr}\\b", i.meaning_1):
        #                 total_matches +=  1
        #                 matching_lemmas.append(i.lemma_1)
        #                 print_check_assign(i, constr)

        #! check for adj with relative_pronouns in the meaning which ends on pp
        # if (
        #     i.meaning_1
        #     and i.example_1
        #     and i.pos == "adj"
        #     and re.findall("\\bcomp\\b", i.grammar)
        #     and "bahubbīhi" not in i.compound_type
        #     and i.id not in g.bahubbihi_dict["no"]
        #     and i.id not in g.bahubbihi_dict["maybe"]
        # ):
        #     # check if the last word of the construction is a noun
        #     constr = clean_construction(i.construction)
        #     constr_list = constr.split(" + ")

        #     if constr_list[-1] in g.pp_set:
                
        #         # check if there is a relative prounoun
        #         for rel_pr in g.relative_pronouns:
        #             if re.findall(f"\\b{rel_pr}\\b", i.meaning_1):
        #                 total_matches +=  1
        #                 matching_lemmas.append(i.lemma_1)
        #                 print_check_assign(i, constr)

        #! check for noun_or_adjective with taddhita "ka|ika|aka"
        # if (
        #     i.meaning_1
        #     and i.example_1
        #     and any (pos in i.pos for pos in g.noun_or_adjective)
        #     and re.findall("\\bcomp\\b", i.grammar)
        #     and "bahubbīhi" not in i.compound_type
        #     and i.derivative == "taddhita"
        #     and "ka" in i.suffix
        #     and i.id not in g.bahubbihi_dict["no"]
        #     and i.id not in g.bahubbihi_dict["maybe"]
        #     and "name of" not in i.meaning_1
        # ):
            
        #     # check if the last word of the construction is a noun
        #     constr = clean_construction(i.construction)

        #     total_matches +=  1
        #     matching_lemmas.append(i.lemma_1)
        #     print_check_assign(i, constr)

        #! check for adjective comp with prefix "sa" for making them bahubbīhi
        if (
            i.meaning_1
            and i.example_1
            and i.pos == "adj"
            and re.findall("\\bcomp\\b", i.grammar)
            and "bahubbīhi" not in i.compound_type
            and i.construction.startswith("sa +")
            and i.id not in g.bahubbihi_dict["no"]
            and i.id not in g.bahubbihi_dict["maybe"]
        ):
            
            # check if the last word of the construction is a noun
            constr = clean_construction(i.construction)

            total_matches +=  1
            matching_lemmas.append(i.lemma_1)
            print_check_assign(i, constr)

        #! check for adjective not comp with prefix "sa" for making them kammadhāraya > bahubbīhi 
        # if (
        #     i.meaning_1
        #     and i.example_1
        #     and i.pos == "adj"
        #     and not re.findall("\\bcomp\\b", i.grammar)
        #     and i.construction.startswith("sa +")
        #     and i.id not in g.bahubbihi_dict["no"]
        #     and i.id not in g.bahubbihi_dict["maybe"]
        # ):
            
        #     # check if the last word of the construction is a noun
        #     constr = clean_construction(i.construction)

        #     total_matches +=  1
        #     matching_lemmas.append(i.lemma_1)
        #     print_check_assign(i, constr)

    print(f"[green]Total matches found: {total_matches}")

    # Write the list of matching lemmas to a CSV file
    # with open('temp/find_bahubbihis.csv', 'w', newline='') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['Lemma'])  # Write the header
    #     for lemma in matching_lemmas:
    #         writer.writerow([lemma])  # Write each lemma on a new row



def print_check_assign(i: DpdHeadword, constr: str):
    print()
    print(f"- [white]{i.lemma_1}")
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
        pyperclip.copy(i.lemma_1)
        print("committed to db")
    
    if route == "n":
        g.update_no(i.id)
        print("saved to 'no'")

    if route == "m":
        g.update_maybe(i.id)
        print("saved to 'maybe'")


if __name__ == "__main__":
    main()


