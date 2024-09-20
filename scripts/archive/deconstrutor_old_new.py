#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

import json
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, Lookup
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(Lookup).filter(Lookup.deconstructor!="").all()

    old_decon_set = set()
    for i in db:
        old_decon_set.add(i.lookup_key)
    print("decon_set:", len(old_decon_set))

    with open("../deconstructor_go/output/matches.json") as f:
        new_decon = json.load(f)
        print("new_decon:", len(new_decon))
    
    new_decon_set = set(new_decon.keys())
    print("new_decon_set:", len(new_decon_set))
    
    diff1 = old_decon_set.difference(new_decon_set)
    print("diff1", len(diff1))

    diff2 = new_decon_set.difference(old_decon_set)
    print("diff2", len(diff2))

    intersection = new_decon_set.intersection(old_decon_set)
    print("intersection", len(intersection))

    sym_diff = new_decon_set.symmetric_difference(old_decon_set)
    print("sym_diff", len(sym_diff))

    # print(diff1)
    # print()
    # print(diff2)





if __name__ == "__main__":
    main()
