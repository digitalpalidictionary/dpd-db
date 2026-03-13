#!/usr/bin/env python3

"""Populate the `see` column of the lookup table from see.tsv."""

from collections import defaultdict
from typing import DefaultDict

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv
from tools.update_test_add import update_test_add


class GlobalVars:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.see_dict: DefaultDict[str, set[str]] = defaultdict(set)
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)
        self.lookup_table: list[Lookup] = self.db_session.query(Lookup).all()


def load_see_dict(g: GlobalVars) -> None:
    """Turn see.tsv into a dictionary of see_word -> set of headwords."""
    pr.green_tmr("loading see tsv")
    see_tsv = read_tsv(g.pth.see_path)
    see_dict: DefaultDict[str, set[str]] = defaultdict(set)
    for see_word, headword in see_tsv[1:]:
        see_dict[see_word].add(headword)
    g.see_dict = see_dict
    pr.yes(len(see_dict))


def add_see(g: GlobalVars) -> None:
    """Three-tier update/test/add for the see column."""
    pr.green_tmr("update test add")
    update_set, test_set, add_set = update_test_add(g.lookup_table, g.see_dict)
    pr.yes("")

    lookup_table_update_test = (
        g.db_session.query(Lookup).filter(Lookup.lookup_key.in_(update_set)).all()
    )

    pr.green_tmr("update")
    if update_set:
        for i in lookup_table_update_test:
            if i.lookup_key in update_set:
                sorted_see = pali_list_sorter(g.see_dict[i.lookup_key])
                i.see_pack(sorted_see)

            elif i.lookup_key in test_set:
                if is_another_value(i, "see"):
                    i.see = ""
                else:
                    g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.green_tmr("add")
    if add_set:
        add_to_db = []
        for see_word, headwords in g.see_dict.items():
            if see_word in add_set:
                add_me = Lookup()
                add_me.lookup_key = see_word
                add_me.see_pack(pali_list_sorter(headwords))
                add_to_db.append(add_me)
        g.db_session.add_all(add_to_db)
    pr.yes(len(add_set))


def main() -> None:
    pr.tic()
    pr.yellow_title("add see entries to lookup table")
    g = GlobalVars()
    load_see_dict(g)
    add_see(g)
    g.db_session.commit()
    g.db_session.close()
    pr.toc()


if __name__ == "__main__":
    main()
