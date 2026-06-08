#!/usr/bin/env python3

"""Compile data for English to Pāḷi dictionary and add to the Lookup table."""

import re
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.configger import config_read
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.printer import printer as pr

POS_EXCLUDE = frozenset({"abbrev", "cs", "letter", "root", "suffix", "ve"})


@dataclass
class GlobalVars:
    db_session: Session
    dpd_db: list[DpdHeadword]
    roots_db: list[DpdRoot]
    epd_data_dict: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)


def compile_headwords_data(g: GlobalVars) -> None:
    """Compile meanings and sutta names in DpdHeadword."""
    pr.green_title("compiling headwords data")

    for counter, i in enumerate(g.dpd_db):
        if i.meaning_1 and i.pos not in POS_EXCLUDE:
            meaning_plus_case = make_meaning_plus_case(i)
            epd_data = (i.lemma_clean, i.pos, meaning_plus_case)
            for meaning in make_clean_meaning_list(i):
                if meaning:
                    g.epd_data_dict.setdefault(meaning, []).append(epd_data)

        if counter % 10000 == 0:
            pr.counter(counter, len(g.dpd_db), i.lemma_1)


def compile_roots_data(g: GlobalVars) -> None:
    """Compile root meanings in DpdRoot."""
    pr.green_tmr("compiling roots data")

    counter = 0
    for i in g.roots_db:
        root_meanings_list: list[str] = i.root_meaning.split(", ")
        epd_data = (i.root, "root", i.root_meaning)
        for root_meaning in root_meanings_list:
            g.epd_data_dict.setdefault(root_meaning, []).append(epd_data)
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
    return meanings_clean.split(";")


def make_meaning_plus_case(i: DpdHeadword) -> str:
    """Return meaning and optionally (plus_case)"""

    if i.plus_case:
        return f"{i.meaning_1} ({i.plus_case})"
    else:
        return i.meaning_1


def add_to_lookup_table(g: GlobalVars) -> None:
    """Add EPD data to lookup table."""

    pr.green_title("saving to Lookup table")
    pr.white_tmr("syncing epd column")
    result = sync_lookup_column(g.db_session, "epd", g.epd_data_dict)
    pr.yes(result.updated + result.inserted)


def main() -> None:
    pr.tic()
    pr.yellow_title("generating epd data for lookup table")

    if config_read("generate", "epd", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pr.green_tmr("making global data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = sorted(
        db_session.query(DpdHeadword).all(),
        key=lambda x: pali_sort_key(x.lemma_1),
    )
    roots_db = db_session.query(DpdRoot).all()
    g = GlobalVars(db_session=db_session, dpd_db=dpd_db, roots_db=roots_db)
    pr.yes("")

    compile_headwords_data(g)
    compile_roots_data(g)
    add_to_lookup_table(g)
    pr.toc()


if __name__ == "__main__":
    main()
