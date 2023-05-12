#!/usr/bin/env python3
#coding: utf-8

import pickle
import json
import re
import pandas as pd
import csv

from rich import print


from tools.timeis import tic, toc, bip, bop
from db.get_db_session import get_db_session
from db.models import PaliRoot, Sandhi, PaliWord, DerivedData
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths as PTH


def inflection_to_headwords():
    tic()
    print("[bright_yellow]inflection to headwords dict")
    bip()
    message = "all tipitaka words set"
    print(f"[green]{message:<30}", end="")
    with open(PTH.tipitaka_word_count_path) as f:
        reader = csv.reader(f, delimiter="\t")
        all_tipitaka_words: set = set([row[0] for row in reader])
    print(f"{len(all_tipitaka_words):>10,}{bop():>10}")

    bip()
    message = "adding pali words"
    print(f"[green]{message:<30}", end="")

    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord).all()
    dd_db = db_session.query(DerivedData).all()
    i2h_dict = {}

    for counter, (i, dd) in enumerate(zip(dpd_db, dd_db)):
        inflections = dd.inflections_list
        for inflection in inflections:
            if inflection in all_tipitaka_words:
                if inflection not in i2h_dict:
                    i2h_dict[inflection] = {i.pali_1}
                else:
                    i2h_dict[inflection].add(i.pali_1)

    print(f"{len(dpd_db):>10,}{bop():>10}")

    # add roots
    bip()
    message = "adding roots"
    print(f"[green]{message:<30}", end="")
    roots_db = db_session.query(PaliRoot).all()

    for r in roots_db:

        # add clean roots
        if r.root_clean not in i2h_dict:
            i2h_dict[r.root_clean] = {r.root_clean}
        else:
            i2h_dict[r.root_clean].add(r.root_clean)

    print(f"{len(roots_db):>10,}{bop():>10}")

    # add sandhi
    bip()
    message = "adding sandhi"
    print(f"[green]{message:<30}", end="")
    sandhi_db = db_session.query(Sandhi).all()

    for i in sandhi_db:

        # add clean roots
        if i.sandhi not in i2h_dict:
            i2h_dict[i.sandhi] = {i.sandhi}
        else:
            i2h_dict[i.sandhi].add(i.sandhi)

    print(f"{len(sandhi_db):>10,}{bop():>10}")

    bip()
    message = "saving to tsv"
    print(f"[green]{message:<30}", end="")
    with open(PTH.inflection_to_headwords_dict_path, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["inflection", "headwords"])
        for k, v in i2h_dict.items():
            v = sorted(v, key=pali_sort_key)
            writer.writerow([k, v])
    print(f"{len(i2h_dict):>10,}{bop():>10}")

    toc()
    return


def main():
    inflection_to_headwords()


if __name__ == "__main__":
    main()