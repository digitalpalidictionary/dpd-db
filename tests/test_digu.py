#!/usr/bin/env python3

"""Find numerals in compounds, and change the compound type to digu."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.meaning_construction import clean_construction, make_meaning_combo
from tools.paths import ProjectPaths
from tools.tsv_read_write import write_tsv_list, read_tsv_dot_dict, write_tsv_dot_dict


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    cardinal_set = set()
    cardinal_in_construction_set = set()
    all_parts_are_cardinal_set = set()
    pos_exceptions = ["card", "ind", "ordin"]
    digu_tsv_data: list[list[str]]
    pali_id_dict: dict[str, int]

g = ProgData()


def main():
    print("[bright_yellow]find all possible digu samāsa")

    if g.pth.digu_path.exists:
        g.digu_tsv_data = read_tsv_dot_dict(g.pth.digu_path)
        print(g.digu_tsv_data) 
    else:
        make_dict_of_cardinals()
        find_cardinals_in_construction()
        remove_identical_members()
        write_to_tsv()


def make_dict_of_cardinals():
    """Make a list of all cardinal numbers in the db."""
    print(f"[green]{'making list of cardinals':40}", end="")
    
    for i in g.db:
        if i.pos == "card":
            g.cardinal_set.add(i.lemma_clean)
    
    print(len(g.cardinal_set))


def find_cardinals_in_construction():
    """Find all the constructions containing a known cardinal."""
    print(f"[green]{'finding cardinals in construction':<40}", end="")
    
    for i in g.db:
        if (
            re.findall("\\bcomp\\b", i.grammar)
            and "digu" not in i.compound_type 
        ):
            construction_clean = clean_construction(i.construction)
            construction_parts = construction_clean.split(" + ")
            
            all_parts_are_card = True
            for part in construction_parts:
                if part in g.cardinal_set:
                    g.cardinal_in_construction_set.add(i.lemma_1)
                else:
                    all_parts_are_card = False
            
            if all_parts_are_card:
                g.all_parts_are_cardinal_set.add(i.lemma_1)
    
    print(len(g.cardinal_in_construction_set))


def remove_identical_members():
    """Remove compound cardinal numbers from the list."""
    print(f"[green]{'removing compound cardinals':<40}", end="")

    for i in g.cardinal_in_construction_set.copy():
        if i in g.all_parts_are_cardinal_set:
            g.cardinal_in_construction_set.remove(i)

    print(len(g.cardinal_in_construction_set))


def write_to_tsv():
    "Write the data to tsv."
    print(f"[green]{'writing to tsv':<40}", end="")

    data_list = []
    header = ["lemma_1", "pos", "meaning", "construction", "compound_type", "compound_construction"]
    
    for i in g.db:
        if i.lemma_1 in g.cardinal_in_construction_set:
            data_list.append(
                [i.lemma_1, i.pos, make_meaning_combo(i), i.construction, i.compound_type, i.compound_construction])
    
    write_tsv_list(str(g.pth.digu_path), header, data_list)

    print("ok")


# -------------------------------------------------------
# fix id functions 
# -------------------------------------------------------


def fix_missing_id():
    if g.pth.digu_path.exists:
        g.digu_tsv_data = read_tsv_dot_dict(g.pth.digu_path)
        make_id_dict(g)
        add_id_tsv_data(g)
        write_back_to_tsv(g)


def make_id_dict(g):
    g.pali_id_dict = {}
    for i in g.db:
        g.pali_id_dict[i.lemma_1] = i.id


def add_id_tsv_data(g):
    for i in g.digu_tsv_data:
        print(i)
        i["id"] = g.pali_id_dict[i.lemma_1]
        print(i)

def write_back_to_tsv(g):
    write_tsv_dot_dict(g.pth.digu_path, g.digu_tsv_data)

# -------------------------------------------------------


if __name__ == "__main__":
    main()
    # fix_missing_id()
    # print()