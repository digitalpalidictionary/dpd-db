#!/usr/bin/env python3

"""Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords."""

import csv

from rich import print

from tools.tic_toc import tic, toc, bip, bop
from db.get_db_session import get_db_session
from db.models import PaliRoot, PaliWord, DerivedData, Sandhi
from db.models import InflectionToHeadwords
from tools.pali_sort_key import pali_sort_key
from tools.paths import ProjectPaths
from tools.sandhi_words import make_words_in_sandhi_set
from tools.headwords_clean_set import make_clean_headwords_set


def inflection_to_headwords(pth: ProjectPaths):
    tic()
    print("[bright_yellow]inflection to headwords dict")

    bip()
    print(f"[green]{'querying db':<30}", end="")
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    dd_db = db_session.query(DerivedData).all()
    sandhi_db = db_session.query(Sandhi).all()
    print(f"{len(dpd_db):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all tipitaka words set':<30}", end="")
    with open(pth.tipitaka_word_count_path) as f:
        reader = csv.reader(f, delimiter="\t")
        all_tipitaka_words: set = set([row[0] for row in reader])
    print(f"{len(all_tipitaka_words):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all words in sandhi set':<30}", end="")
    words_in_sandhi_set: set = make_words_in_sandhi_set(sandhi_db)
    print(f"{len(words_in_sandhi_set):>10,}{bop():>10}")

    bip()
    print(f"[green]{'clean headwords set':<30}", end="")
    clean_headwords_set: set = make_clean_headwords_set(dpd_db)
    print(f"{len(clean_headwords_set):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all words set':<30}", end="")
    all_words_set: set = all_tipitaka_words | words_in_sandhi_set
    all_words_set.update(clean_headwords_set)
    print(f"{len(all_words_set):>10,}{bop():>10}")

    bip()
    message = "adding pali words"
    print(f"[green]{message:<30}", end="")

    i2h_dict = {}

    for __counter__, (i, dd) in enumerate(zip(dpd_db, dd_db)):
        inflections = dd.inflections_list
        for inflection in inflections:
            if inflection in all_words_set:
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

    # !!! FIXME add proper roots headwords 

    for r in roots_db:

        # add clean roots
        if r.root_clean not in i2h_dict:
            i2h_dict[r.root_clean] = {r.root_clean}
        else:
            i2h_dict[r.root_clean].add(r.root_clean)

        # add roots no sign
        if r.root_no_sign not in i2h_dict:
            i2h_dict[r.root_no_sign] = {r.root_clean}
        else:
            i2h_dict[r.root_no_sign].add(r.root_clean)

    print(f"{len(roots_db):>10,}{bop():>10}")

    bip()
    message = "saving to tsv"
    print(f"[green]{message:<30}", end="")
    with open(pth.tpr_i2h_tsv_path, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["inflection", "headwords"])
        for k, v in i2h_dict.items():
            v = sorted(v, key=pali_sort_key)
            v = ",".join(v)
            writer.writerow([k, v])
    print(f"{len(i2h_dict):>10,}{bop():>10}")

    add_i2h_to_db(db_session, i2h_dict)
    toc()


def add_i2h_to_db(db_session, i2h_dict):
    bip()
    print(f"[green]{'adding to db':<30}", end="")

    add_to_db = []

    for inflection, headwords in i2h_dict.items():
        headwords = sorted(headwords, key=pali_sort_key)
        headwords_string = ",".join(headwords)
        i2h_data = InflectionToHeadwords(
            inflection=inflection,
            headwords=headwords_string)
        add_to_db.append(i2h_data)

    db_session.execute(InflectionToHeadwords.__table__.delete())
    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()
    print(f"{len(i2h_dict):>10,}{bop():>10}")


def main():
    pth = ProjectPaths()
    inflection_to_headwords(pth)


if __name__ == "__main__":
    main()
