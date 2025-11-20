#!/usr/bin/env python3

"""Compile data for English to Pāḷi dictionary and add to the Lookup table."""

import re

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot, Lookup
from tools.configger import config_test
from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.update_test_add import update_test_add


class GlobalVars:
    pr.tic()
    pr.title("generating epd data for lookup table")
    pr.green("making global data")
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)

    dpd_db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    dpd_db = sorted(dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    dpd_db_length = len(dpd_db)

    roots_db: list = db_session.query(DpdRoot).all()
    roots_db_length = len(roots_db)

    pos_exclude_list = ["abbrev", "cs", "letter", "root", "suffix", "ve"]
    epd_data_dict: dict[str, list[tuple[str, str, str]]] = {}

    pr.yes("")


def compile_headwords_data(g: GlobalVars):
    """Compile meanings and sutta names in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.meaning_1 and i.pos not in g.pos_exclude_list:
            meanings_list = make_clean_meaning_list(i)
            for meaning in meanings_list:
                meaning_plus_case = make_meaning_plus_case(i)
                epd_data = (i.lemma_clean, i.pos, meaning_plus_case)

                if meaning and meaning in g.epd_data_dict.keys():
                    g.epd_data_dict[meaning].append(epd_data)
                else:
                    g.epd_data_dict[meaning] = [epd_data]

        if counter % 10000 == 0:
            pr.counter(counter, g.dpd_db_length, i.lemma_1)


def compile_roots_data(g: GlobalVars):
    """Compile root meanings in DpdRoot."""
    pr.green("compiling roots data")

    counter = 0
    for i in g.roots_db:
        root_meanings_list: list = i.root_meaning.split(", ")

        for root_meaning in root_meanings_list:
            epd_data = (i.root, "root", i.root_meaning)
            if root_meaning in g.epd_data_dict.keys():
                g.epd_data_dict[root_meaning].append(epd_data)
            else:
                g.epd_data_dict[root_meaning] = [epd_data]
            counter += 1

    pr.yes(counter)


def make_clean_meaning_list(i: DpdHeadword) -> list[str]:
    "Cleanup meaning_1"

    # remove double ??
    meanings_clean = re.sub(r"\?\?", "", i.meaning_1)
    # remove all space brackets
    meanings_clean = re.sub(r" \(.+?\)", "", meanings_clean)
    # remove all brackets space
    meanings_clean = re.sub(r"\(.+?\) ", "", meanings_clean)
    # remove space at start and fin
    meanings_clean = re.sub(r"(^ | $)", "", meanings_clean)
    # remove double spaces
    meanings_clean = re.sub(r"  ", " ", meanings_clean)
    # remove space around ;
    meanings_clean = re.sub(r" ;|; ", ";", meanings_clean)
    # remove i.e.
    meanings_clean = re.sub(r"i\.e\. ", "", meanings_clean)
    # remove !
    meanings_clean = re.sub(r"!", "", meanings_clean)
    # remove ?
    meanings_clean = re.sub(r"\\?", "", meanings_clean)
    return meanings_clean.split(";")


def make_meaning_plus_case(i: DpdHeadword):
    """Return meaning and optionally (plus_case)"""

    if i.plus_case:
        return f"{i.meaning_1} ({i.plus_case})"
    else:
        return i.meaning_1


def add_to_lookup_table(g: GlobalVars):
    """Add EPD data to lookup table."""

    pr.green_title("saving to Lookup table")

    pr.white("update test or add")
    lookup_table = g.db_session.query(Lookup).all()
    results = update_test_add(lookup_table, g.epd_data_dict)
    update_set, test_set, add_set = results
    pr.yes("")

    pr.white("updating and deleting")
    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.epd_pack(g.epd_data_dict[i.lookup_key])
        elif i.lookup_key in test_set:
            if is_another_value(i, "epd"):
                i.epd = ""
            else:
                g.db_session.delete(i)
    pr.yes(len(update_set))

    pr.white("adding")
    # add
    add_to_db = []
    for key, data in g.epd_data_dict.items():
        if key in add_set:
            add_me = Lookup()
            add_me.lookup_key = key
            add_me.epd_pack(data)
            add_to_db.append(add_me)
    pr.yes(len(add_set))

    pr.white("committing")
    g.db_session.add_all(add_to_db)
    g.db_session.commit()
    pr.yes("ok")


def main():
    g = GlobalVars()
    compile_headwords_data(g)
    compile_roots_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
