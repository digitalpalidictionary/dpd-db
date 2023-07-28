#!/usr/bin/env python3

"""A simple system of
1. inflection to headwords lookup
2. compound deconstruction
4. dictionary data for EBTS."""

import json

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord, Sandhi, DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.tic_toc import tic, toc
from tools.cst_sc_text_sets import make_sc_text_set
from tools.meaning_construction import make_meaning_html
from tools.meaning_construction import summarize_constr
from tools.paths import ProjectPaths as PTH


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

    """Get all the required info from the db."""

    print(f"[green]{'making db searches':<40}", end="")

    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord)
    dd_db = db_session.query(DerivedData)
    sandhi_db = db_session.query(Sandhi)
    print("OK")

    # -------------------------------------------------------------------------------

    print(f"[green]{'making sandhi splits set':<40}", end="")

    # inflections to headwords dict
    sandhi_splits_set: set = set()
    matched = set()

    for i in sandhi_db:
        if i.sandhi in tbw_word_set:
            matched.add(i.sandhi)
            splits = i.split_list
            for split in splits:
                sandhi_splits_set.update(split.split(" + "))

    print(f"{len(sandhi_splits_set):,}")

    # -------------------------------------------------------------------------------

    """Make an inflections to headwords dictionary."""
    print(f"[green]{'making inflections to headwords dict':<40}", end="")

    i2h: dict = {}

    for counter, (i, dd) in enumerate(zip(dpd_db, dd_db)):
        assert i.id == dd.id

        inflections = dd.inflections_list
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

    # -------------------------------------------------------------------------------

    # add words with "n" instead of "ṅ"
    # this problem is unique to tbw website

    print(f"{'adding ṅ words with n':<40}", end="")
    nṅdict = {}

    i2h_copy = i2h.copy()
    for inflection, headwords in i2h_copy.items():
        if "ṅ" in inflection:
            inflection_n = inflection.replace("ṅ", "n")
            nṅdict[inflection_n] = inflection
            # if inflection_n not in i2h:
            #     i2h[inflection_n] = headwords
            # else:
            #     i2h[inflection_n] += headwords

    print(f"{len(nṅdict):,}")

    with open(PTH.nṅ_tsv_path, "w") as f:
        f.write("n\tṅ\n")
        for n, ṅ in nṅdict.items():
            f.write(f"{n}\t{ṅ}\n")

    # -------------------------------------------------------------------------------

    unmatched = tbw_word_set - matched
    print(f"[green]{'unmatched':<40}{len(unmatched):,}")

    print(f"[green]{'writing i2h.json':<40}", end="")
    with open(PTH.i2h_json_path, "w") as f:
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
            string += make_meaning_html(i)
            if i.meaning_1:
                if i.construction:
                    string += f" [{summarize_constr(i)}]"

            dpd_dict[i.pali_1] = string

    dpd_dict = dict(sorted(dpd_dict.items(), key=lambda x: pali_sort_key(x[0])))
    print(f"{len(dpd_dict):,}")

    # -------------------------------------------------------------------------------

    print(f"[green]{'writing dpd_ebts.json':<40}", end="")
    with open(PTH.dpd_ebts_json_path, "w") as f:
        json.dump(dpd_dict, f, ensure_ascii=False, indent=0)
        print("OK")

    # -------------------------------------------------------------------------------

    sandhi_dict = {}

    for i in sandhi_db:
        if i.sandhi not in dpd_dict and i.sandhi in tbw_word_set:
            splits = i.split_list
            string = "<br>".join(splits)
            sandhi_dict[i.sandhi] = string

    sandhi_dict = dict(sorted(sandhi_dict.items(), key=lambda x: pali_sort_key(x[0])))

    print(f"[green]{'writing sandhi.json':<40}", end="")
    with open(PTH.sandhi_json_path, "w") as f:
        json.dump(sandhi_dict, f, ensure_ascii=False, indent=0)
        print("OK")

    # -------------------------------------------------------------------------------

    toc()


if __name__ == "__main__":
    main()
