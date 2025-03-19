#!/usr/bin/env python3

"""Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords."""

from collections import defaultdict
from typing import DefaultDict

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv
from tools.update_test_add import update_test_add
from tools.printer import p_green, p_title, p_yes


class ProgData:
    pth: ProjectPaths = ProjectPaths()
    spellings_dict: DefaultDict[str, set[str]]
    db_session: Session = get_db_session(pth.dpd_db_path)
    lookup_table: list[Lookup] = db_session.query(Lookup).all()


def load_spelling_dict(pd: ProgData):
    """Turn the spelling_mistakes.tsv into a dictionary"""
    p_green("loading spelling tsv")

    spellings_tsv = read_tsv(pd.pth.spelling_mistakes_path)
    spellings_dict = defaultdict(set)
    for spelling, correction in spellings_tsv[1:]:
        spellings_dict[spelling].add(correction)
    pd.spellings_dict = spellings_dict
    p_yes(len(spellings_dict))


def add_spellings(pd: ProgData):
    p_green("update test add")
    update_set, test_set, add_set = update_test_add(pd.lookup_table, pd.spellings_dict)
    p_yes("")

    lookup_table_update_test = (
        pd.db_session.query(Lookup).filter(Lookup.lookup_key.in_(update_set)).all()
    )
    p_green("update")
    # update test add
    if update_set:
        for i in lookup_table_update_test:
            if i.lookup_key in update_set:
                sorted_spelling = pali_list_sorter(pd.spellings_dict[i.lookup_key])
                i.spelling_pack(sorted_spelling)

            # test_set
            elif i.lookup_key in test_set:
                if is_another_value(i, "spelling"):
                    i.spelling = ""
                else:
                    pd.db_session.delete(i)
    p_yes(len(update_set))

    p_green("add")

    if add_set:
        add_to_db = []
        for mistake, correction in pd.spellings_dict.items():
            if mistake in add_set:
                add_me = Lookup()
                add_me.lookup_key = mistake
                add_me.spelling_pack(pali_list_sorter(correction))
                add_to_db.append(add_me)

        pd.db_session.add_all(add_to_db)
    p_yes(len(add_set))


def main():
    tic()
    p_title("add spelling mistakes to lookup table")
    pd = ProgData()
    load_spelling_dict(pd)
    add_spellings(pd)
    pd.db_session.commit()
    pd.db_session.close()
    toc()


if __name__ == "__main__":
    main()
