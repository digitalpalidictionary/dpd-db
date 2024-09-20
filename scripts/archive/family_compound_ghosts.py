#!/usr/bin/env python3

"""Find phonetic changes because of Sanskrit ṛ"""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, FamilyCompound
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


class ProgData():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    fc_table_set: set
    fc_db_set: set

g = ProgData

def main():
    
    get_all_family_compounds_in_table()
    get_all_family_compounds_in_headwords()
    check_differences()


def get_all_family_compounds_in_table():

    results = g.db_session \
        .query(FamilyCompound.compound_family) \
        .all()
    
    g.fc_table_set = set([tuple[0] for tuple in results])
    print(len(g.fc_table_set))


def get_all_family_compounds_in_headwords():

    results = g.db_session \
        .query(DpdHeadword) \
        .filter(DpdHeadword.family_compound != "") \
        .all()
    
    g.fc_db_set = set()
    for r in results:
        for word in r.family_compound_list:
            g.fc_db_set.add(word)

    print(len(g.fc_db_set))
    
def check_differences():

    diff1 = g.fc_table_set.difference(g.fc_db_set)
    diff2 = g.fc_db_set.difference(g.fc_table_set)
    print(diff1)
    print(len(diff1))
    print(", ".join(diff2))
    print(len(diff2))
    
    pyperclip.copy(db_search_string(diff2, start_end=False))

if __name__ == "__main__":
    main()
