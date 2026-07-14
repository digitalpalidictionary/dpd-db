#!/usr/bin/env python3

"""Find words in early Buddhist texts (EBTs) that are missing from DPD.

Builds a word set from CST + SC + BJT sources, cross-references against
inflections of entries lacking meaning_1 or example_1, then opens each
missing word in Goldendict and copies it to clipboard for manual entry.

Run:
    uv run scripts/add/add_words_ebts.py
"""

from typing import cast

import pyperclip
from rich import print
from sqlalchemy import desc, or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.bjt import make_bjt_text_list
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.goldendict_tools import open_in_goldendict
from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    ebts = [
        "vin1",
        "vin2",
        "vin3",
        "vin4",
        "dn1",
        "dn2",
        "dn3",
        "mn1",
        "mn2",
        "mn3",
        "sn1",
        "sn2",
        "sn3",
        "sn4",
        "sn5",
        "an1",
        "an2",
        "an3",
        "an4",
        "an5",
        "an6",
        "an7",
        "an8",
        "an9",
        "an10",
        "an11",
        "kn1",
        "kn2",
        "kn3",
        "kn4",
        "kn5",
        "kn6",
        "kn7",
        "kn8",
        "kn9",
        "kn10",
        "kn11",
        "kn12",
        "kn13",
        "kn14",
        "kn15",
    ]


def make_ebt_word_set(g: GlobalVars) -> set[str]:
    cst_text_set = make_cst_text_set(g.pth, g.ebts)
    sc_text_set = make_sc_text_set(g.pth, g.ebts)
    bjt_text_set: set[str] = cast(set[str], make_bjt_text_list(g.ebts, "set"))
    all_words = cst_text_set | sc_text_set | bjt_text_set
    pr.green_tmr("all words in ebts")
    pr.yes(len(all_words))
    return all_words


def make_dpd_missing_set(g: GlobalVars) -> set[str]:
    pr.green_tmr("missing words in dpd")
    db = g.db_session.query(DpdHeadword).all()
    missing_words: list[str] = []
    for i in db:
        if not i.meaning_1 or not i.example_1:
            missing_words.extend(i.inflections_list)
    missing_words_set = set(missing_words)
    pr.yes(len(missing_words_set))
    return missing_words_set


def main() -> None:
    pr.yellow_title("find missing words in ebts")
    pr.white(
        "iterate through missing words in EBTs; "
        "press q to quit, any other key to continue"
    )

    g = GlobalVars()
    ebt_word_set = make_ebt_word_set(g)
    dpd_missing_words = make_dpd_missing_set(g)

    pr.green_tmr("missing words in ebts")
    missing_words_in_ebts = ebt_word_set & dpd_missing_words
    pr.yes(len(missing_words_in_ebts))

    ebt_db = (
        g.db_session.query(DpdHeadword)
        .filter(or_(DpdHeadword.meaning_1 == "", DpdHeadword.example_1 == ""))
        .filter(~DpdHeadword.lemma_1.regexp_match(r"\d"))
        .order_by(desc(DpdHeadword.ebt_count))
        .all()
    )

    counter = 0
    for i in ebt_db:
        for inflection in i.inflections_list_all:
            if inflection in missing_words_in_ebts:
                counter += 1
                if counter % 5 == 0:
                    pr.white("press q to quit")
                open_in_goldendict(inflection)
                pyperclip.copy(inflection)
                print(inflection)
                user_input = input()
                if user_input == "q":
                    return


if __name__ == "__main__":
    main()
