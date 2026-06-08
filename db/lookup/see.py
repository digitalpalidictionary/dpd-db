#!/usr/bin/env python3

"""Populate the `see` column of the lookup table from see.tsv."""

from collections import defaultdict
from typing import DefaultDict

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.tsv_read_write import read_tsv


class GlobalVars:
    def __init__(self) -> None:
        self.pth: ProjectPaths = ProjectPaths()
        self.see_dict: DefaultDict[str, set[str]] = defaultdict(set)
        self.db_session: Session = get_db_session(self.pth.dpd_db_path)


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
    """Add/update the see column and clear stale entries."""
    pr.green_tmr("syncing see column")
    data = {
        see_word: pali_list_sorter(headwords)
        for see_word, headwords in g.see_dict.items()
    }
    result = sync_lookup_column(g.db_session, "see", data)
    pr.yes(result.updated + result.inserted)


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
