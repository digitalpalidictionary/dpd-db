#!/usr/bin/env python3.11

import json

from rich import print

# from html_components import render_dpd_defintion_templ
# from helpers import get_paths, ResourcePaths
from db.get_db_session import get_db_session
from db.models import PaliWord, Sandhi, DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.timeis import tic, toc
from tools.make_cst_sc_text_sets import make_sc_text_set
from tools.meaning_construction import make_meaning
from tools.meaning_construction import summarize_constr
from tools.pali_sort_key import pali_sort_key



def main():
    tic()
    print("[bright_yellow]exporting json files for the buddhas words website")

    print(f"[green]{'making sutta central ebts word list':<40}", end="")

    sc_text_list = [
        "vin1", "vin2", "vin3", "vin4", "vin5",
        "dn1", "dn2", "dn3",
        "mn1", "mn2", "mn3",
        "sn1", "sn2", "sn3", "sn4", "sn5",
        "an1", "an2", "an3", "an4", "an5",
        "an6", "an7", "an8", "an9", "an10", "an11",
        "kn1", "kn2", "kn3", "kn4", "kn5",
        "kn8", "kn9",
        ]

    tbw_word_set: set = make_sc_text_set(sc_text_list)
    print(f"{len(tbw_word_set):,}")

    # -------------------------------------------------------------------------------

    print(f"[green]{'making db searches':<40}", end="")

    # build a dict of inflections to headwords
    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord)
    dd_db = db_session.query(DerivedData)
    sandhi_db = db_session.query(Sandhi)
    print("OK")

    # -------------------------------------------------------------------------------

    print(f"[green]{'making inflections to headwords dict':<40}")

    print(f"{'adding sandhi and splits':<40}", end="")

    # inflections to headwords dict
    i2h: dict = {}
    sandhi_splits_set: set = set()
    matched = set()

    for i in sandhi_db:
        if i.sandhi in tbw_word_set:
            matched.add(i.sandhi)

            test1 = "spelling" not in i.split
            test2 = "variant" not in i.split
            if test1 & test2:
                splits = json.loads(i.split)
                for split in splits:
                    sandhi_splits_set.update(split.split(" + "))

            if i.sandhi not in i2h:
                i2h[i.sandhi] = [i.sandhi]
            else:
                i2h[i.sandhi] += [i.sandhi]

    print(f"{len(sandhi_splits_set):,}")

    print(f"{'adding inflections':<40}", end="")

    for counter, (i, dd) in enumerate(zip(dpd_db, dd_db)):
        assert i.id == dd.id

        inflections = json.loads(dd.inflections)
        for inflection in inflections:
            test1 = (
                inflection in tbw_word_set or
                inflection in sandhi_splits_set)
            test2 = "(gram)" not in i.meaning_1
            if test1 & test2:
                matched.add(inflection)
                if inflection not in i2h:
                    i2h[inflection] = [i.pali_1]
                else:
                    i2h[inflection] += [i.pali_1]

    print(f"{len(i2h):,}")

    unmatched = tbw_word_set - matched
    print(f"[green]{'unmatched':<40}{len(unmatched):,}")

    print(f"[green]{'writing i2h.json':<40}", end="")
    with open("the_buddhas_words/output/i2h.json", "w") as f:
        json.dump(i2h, f, ensure_ascii=False, indent=0)
        print("OK")

    # -------------------------------------------------------------------------------

    print(f"[green]{'making dpd data json':<40}", end="")

    headwords_set: set = set()
    for key, values in i2h.items():
        headwords_set.update(values)

    dpd_dict = {}

    for i in dpd_db:
        if i.pali_1 in headwords_set:
            string = f"{i.pos}. "
            string += make_meaning(i)
            if i.meaning_1:
                if i.construction:
                    i.construction = i.construction.replace("\n", "<br>")
                    string += f" [{summarize_constr(i)}]"

            dpd_dict[i.pali_1] = string

    dpd_dict = dict(sorted(dpd_dict.items(), key=lambda x: pali_sort_key(x[0])))

    # -------------------------------------------------------------------------------

    sandhi_dict = {}

    for i in sandhi_db:
        if i.sandhi not in dpd_dict and i.sandhi in headwords_set:
            splits = json.loads(i.split)
            string = "\n".join(splits)
            sandhi_dict[i.sandhi] = string

    sandhi_dict = dict(sorted(sandhi_dict.items(), key=lambda x: pali_sort_key(x[0])))
    dpd_dict.update(sandhi_dict)
    print(f"{len(dpd_dict):,}")

    print(f"[green]{'writing dpd_ebts.json':<40}", end="")
    with open("the_buddhas_words/output/dpd_ebts.json", "w") as f:
        json.dump(dpd_dict, f, ensure_ascii=False, indent=0)
        print("OK")

    # -------------------------------------------------------------------------------

    toc()


if __name__ == "__main__":
    main()
