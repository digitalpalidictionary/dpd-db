#!/usr/bin/env python3

"""Find a word in early texts which needs to be added."""

import pyperclip
from rich import print
from sqlalchemy import desc, or_

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.bjt import make_bjt_text_list
from tools.cst_sc_text_sets import make_cst_text_set, make_sc_text_set
from tools.goldendict_tools import open_in_goldendict_os
from tools.paths import ProjectPaths
from tools.printer import p_green, p_title, p_yes


class GlobalVars():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    ebts = [
        "vin1", "vin2", "vin3", "vin4",
        "dn1", "dn2", "dn3",
        "mn1", "mn2", "mn3",
        "sn1", "sn2", "sn3", "sn4", "sn5",
        "an1", "an2", "an3", "an4", "an5",
        "an6", "an7", "an8", "an9", "an10", "an11",
        "kn1", "kn2", "kn3", "kn4", "kn5", 
        "kn6", "kn7", "kn8", "kn9", "kn10",
        "kn11", "kn12", "kn13", "kn14", "kn15",
    ]


def make_ebt_word_set(g: GlobalVars):
    cst_text_set = make_cst_text_set(g.pth, g.ebts)
    sc_text_set = make_sc_text_set(g.pth, g.ebts)
    bjt_text_set: set[str] = make_bjt_text_list(g.ebts, "set")
    all_words = cst_text_set | sc_text_set | bjt_text_set
    p_green("all words in ebts")
    p_yes(len(all_words))
    return all_words


def make_dpd_missing_set(g: GlobalVars):
    p_green("missing words in dpd")
    db = g.db_session.query(DpdHeadword).all()
    missing_words = []
    for i in db:
        if not i.meaning_1 or not i.example_1:
            missing_words.extend(i.inflections_list)
    missing_words = set(missing_words)      
    p_yes(len(missing_words))
    return missing_words

def main():
    p_title("find missing words in ebts")

    g = GlobalVars()
    ebt_word_set = make_ebt_word_set(g)
    dpd_missing_words = make_dpd_missing_set(g)
    
    p_green("missing words in ebts")
    missing_words_in_ebts = ebt_word_set & dpd_missing_words
    p_yes (len(missing_words_in_ebts))

    ebt_db = g.db_session \
        .query(DpdHeadword) \
        .filter(
            or_(
                DpdHeadword.meaning_1 == "",
                DpdHeadword.example_1 == ""
            )
        ) \
        .filter(~DpdHeadword.lemma_1.regexp_match(r"\d")) \
        .order_by(desc(DpdHeadword.ebt_count)) \
        .all()
    
    for i in ebt_db:
        for inflection in i.inflections_list_all:
            if inflection in missing_words_in_ebts:
                open_in_goldendict_os(inflection)
                pyperclip.copy(inflection)
                print(inflection)
                user_input = input()
                if user_input == "x":
                    return

if __name__ == "__main__":
    main()


# TODO add all words in compounds once this list is done. 
