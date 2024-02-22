#!/usr/bin/env python3

"""Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords."""

import csv

from rich import print
from tools.lookup_is_another_value import is_another_value

from tools.tic_toc import tic, toc, bip, bop
from db.get_db_session import get_db_session
from db.models import DpdHeadwords, Lookup
from tools.paths import ProjectPaths
from tools.deconstructed_words import make_words_in_deconstructions
from tools.headwords_clean_set import make_clean_headwords_set
from tools.update_test_add import update_test_add
from tools.pali_sort_key import pali_list_sorter


def inflection_to_headwords(pth: ProjectPaths):
    tic()
    print("[bright_yellow]inflection to headwords dict")

    bip()
    print(f"[green]{'querying db':<30}", end="")
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadwords).all()
    print(f"{len(dpd_db):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all tipitaka words set':<30}", end="")
    with open(pth.tipitaka_word_count_path) as f:
        reader = csv.reader(f, delimiter="\t")
        all_tipitaka_words: set = set([row[0] for row in reader])
    print(f"{len(all_tipitaka_words):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all words in deconstructor set':<30}", end="")
    words_in_deconstructions: set = make_words_in_deconstructions(db_session)
    print(f"{len(words_in_deconstructions):>10,}{bop():>10}")

    bip()
    print(f"[green]{'clean headwords set':<30}", end="")
    clean_headwords_set: set = make_clean_headwords_set(dpd_db)
    print(f"{len(clean_headwords_set):>10,}{bop():>10}")

    bip()
    print(f"[green]{'all words set':<30}", end="")
    all_words_set: set = all_tipitaka_words | words_in_deconstructions
    all_words_set.update(clean_headwords_set)
    print(f"{len(all_words_set):>10,}{bop():>10}")

    bip()
    message = "adding pali words"
    print(f"[green]{message:<30}", end="")

    i2h_dict = {}
    i2h_dict_tpr = {}

    for i in dpd_db:
        inflections = i.inflections_list
        for inflection in inflections:
            if inflection in all_words_set:
                if inflection not in i2h_dict:
                    i2h_dict[inflection] = [i.id]
                    i2h_dict_tpr[inflection] = [i.lemma_1]
                else:
                    i2h_dict[inflection].append(i.id)
                    i2h_dict_tpr[inflection].append(i.lemma_1)

    print(f"{len(dpd_db):>10,}{bop():>10}")

    bip()
    message = "saving to tsv for tpr"
    print(f"[green]{message:<30}", end="")
    with open(pth.tpr_i2h_tsv_path, "w") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(["inflection", "headwords"])

        for inflection, headwords in i2h_dict_tpr.items():
            headwords = pali_list_sorter(headwords)
            headwords = ",".join(headwords)
            writer.writerow([inflection, headwords])
    
    print(f"{len(i2h_dict_tpr):>10,}{bop():>10}")

    add_i2h_to_db(db_session, i2h_dict)
    toc()


def add_i2h_to_db(db_session, i2h_dict):
    bip()
    print(f"[green]{'adding to db':<30}", end="")

    lookup_table = (db_session.query(Lookup).all())
    update_set, test_set, add_set = update_test_add(lookup_table, i2h_dict)

    # update test add
    for i in lookup_table:
        if i.lookup_key in update_set:
            i.headwords_pack(sorted(i2h_dict[i.lookup_key]))
        elif i.lookup_key in test_set:
            if is_another_value(i, "headwords"):
                i.headwords = ""
            else:
                db_session.delete(i)    
    
    db_session.commit()

    # add
    add_to_db = []
    for inflection, ids in i2h_dict.items():    
        if inflection in add_set:
            add_me = Lookup()
            add_me.lookup_key = inflection
            add_me.headwords_pack(sorted(ids))
            add_to_db.append(add_me)

    db_session.add_all(add_to_db)
    db_session.commit()
    db_session.close()

    print(f"{len(i2h_dict):>10,}{bop():>10}")


def main():
    pth = ProjectPaths()
    inflection_to_headwords(pth)


if __name__ == "__main__":
    main()
