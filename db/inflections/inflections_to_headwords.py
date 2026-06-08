#!/usr/bin/env python3

"""
Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords.

Add the same data to the lookup table of the db.
"""

import csv
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword

from tools.all_tipitaka_words import make_all_tipitaka_word_set
from tools.configger import config_read
from tools.deconstructed_words import make_words_in_deconstructions
from tools.headwords_clean_set import make_clean_headwords_set
from tools.lookup_sync import sync_lookup_column
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.printer import printer as pr


@dataclass
class GlobalVars:
    pth: ProjectPaths
    db_session: Session
    dpd_db: list[DpdHeadword]
    all_tipitaka_word_set: set[str] = field(default_factory=set)
    deconstructions_word_set: set[str] = field(default_factory=set)
    clean_headwords_set: set[str] = field(default_factory=set)
    all_words_set: set[str] = field(default_factory=set)
    i2h_dict: dict[str, list[int]] = field(default_factory=dict)
    i2h_dict_tpr: dict[str, list[str]] = field(default_factory=dict)


def inflection_to_headwords(g: GlobalVars) -> None:
    """Make a dictionary of inflections: [headwords]."""

    pr.green_tmr("making inflections2headwords dict")

    for i in g.dpd_db:
        inflections = i.inflections_list_all  # include api ca eva iti as well
        for inflection in inflections:
            if inflection in g.all_words_set:
                if inflection not in g.i2h_dict:
                    g.i2h_dict[inflection] = [i.id]
                    g.i2h_dict_tpr[inflection] = [i.lemma_1]
                elif i.id not in g.i2h_dict[inflection]:
                    g.i2h_dict[inflection].append(i.id)
                    g.i2h_dict_tpr[inflection].append(i.lemma_1)

    pr.yes(len(g.i2h_dict))


def save_i2h_for_tpr(g: GlobalVars) -> None:
    """Save inflections2headwords for Tipitaka Pali Reader."""

    pr.green_tmr("saving to tsv for tpr")

    with g.pth.tpr_i2h_tsv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["inflection", "headwords"])

        for inflection, headwords in g.i2h_dict_tpr.items():
            writer.writerow([inflection, ",".join(pali_list_sorter(headwords))])

    pr.yes(len(g.i2h_dict_tpr))


def add_i2h_to_db(g: GlobalVars) -> None:
    """Add inflections2headwords to the lookup table."""

    pr.green_tmr("syncing headwords column")
    data = {inflection: sorted(set(ids)) for inflection, ids in g.i2h_dict.items()}
    result = sync_lookup_column(g.db_session, "headwords", data)
    g.db_session.close()
    pr.yes(result.updated + result.inserted)


def main() -> None:
    pr.tic()
    pr.yellow_title("inflection to headwords")
    if config_read("generate", "inflections_to_headwords", "yes") == "no":
        pr.green_title("disabled in config.ini")
        pr.toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    g = GlobalVars(pth, db_session, db_session.query(DpdHeadword).all())

    pr.green_tmr("making all all_tipitaka_word_set")
    g.all_tipitaka_word_set = make_all_tipitaka_word_set()
    pr.yes(len(g.all_tipitaka_word_set))

    pr.green_tmr("making all deconstructed words set")
    g.deconstructions_word_set = make_words_in_deconstructions(g.db_session)
    pr.yes(len(g.deconstructions_word_set))

    pr.green_tmr("making clean headwords set")
    g.clean_headwords_set = make_clean_headwords_set(g.dpd_db)
    pr.yes(len(g.clean_headwords_set))

    pr.green_tmr("making all words set")
    g.all_words_set = (
        g.all_tipitaka_word_set | g.deconstructions_word_set | g.clean_headwords_set
    )
    pr.yes(len(g.all_words_set))

    inflection_to_headwords(g)
    save_i2h_for_tpr(g)
    add_i2h_to_db(g)

    pr.toc()


if __name__ == "__main__":
    main()
