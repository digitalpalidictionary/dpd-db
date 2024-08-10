#!/usr/bin/env python3

"""Save a TSV of every inflection found in texts or deconstructed compounds
and matching corresponding headwords."""

from collections import defaultdict
from rich import print
from sqlalchemy.orm import Session
from typing import DefaultDict

from db.db_helpers import get_db_session
from db.models import Lookup

from tools.lookup_is_another_value import is_another_value
from tools.pali_sort_key import pali_list_sorter
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.tsv_read_write import read_tsv
from tools.update_test_add import update_test_add


class ProgData():
    pth: ProjectPaths = ProjectPaths()
    variants_dict: DefaultDict[str, set[str]]
    spellings_dict: DefaultDict[str, set[str]]
    db_session: Session = get_db_session(pth.dpd_db_path)
    lookup_table: list[Lookup] = db_session.query(Lookup).all()


def load_variant_dict(pd):
    """Turn the variant_readings.tsv into a dictionary"""
    print(f"[green]{'loading variants tsv':<30}", end="")
    
    variants_tsv = read_tsv(pd.pth.variant_readings_path)
    variants_dict = defaultdict(set)
    for variant, main in variants_tsv[1:]:
        variants_dict[variant].add(main)
    pd.variants_dict = variants_dict
    print(f"{len(variants_dict):>10,}")


def add_variants(pd: ProgData):

    update_set, test_set, add_set = update_test_add(pd.lookup_table, pd.variants_dict)

    lookup_table_update = pd.db_session \
        .query(Lookup) \
        .filter(Lookup.lookup_key.in_(update_set)) \
        .all()
    
    print(f"[green]{'update_set':<30}", end="")

    # update test
    if update_set:
        for i in lookup_table_update:
            if i.lookup_key in update_set:
                sorted_variant = pali_list_sorter(pd.variants_dict[i.lookup_key])
                i.variants_pack(sorted_variant)
            
            # test_set
            elif i.lookup_key in test_set:
                if is_another_value(i, "variant"):
                    i.variant = ""
                else:
                    pd.db_session.delete(i)    
    
    print(f"{len(update_set):>10,}")

    # add
    print(f"[green]{'add set':<30}", end="")

    if add_set:
        add_to_db = []
        for variant, main in pd.variants_dict.items():
            if variant in add_set:
                add_me = Lookup()
                add_me.lookup_key = variant
                add_me.variants_pack(pali_list_sorter(main))
                add_to_db.append(add_me)

        pd.db_session.add_all(add_to_db)

    print(f"{len(add_set):>10,}")


def load_spelling_dict(pd: ProgData):
    """Turn the spelling_mistakes.tsv into a dictionary"""
    print(f"[green]{'loading spelling tsv':<30}", end="")
    
    spellings_tsv = read_tsv(pd.pth.spelling_mistakes_path)
    spellings_dict = defaultdict(set)
    for spelling, correction in spellings_tsv[1:]:
        spellings_dict[spelling].add(correction)
    pd.spellings_dict = spellings_dict
    print(f"{len(spellings_dict):>10,}")


def add_spellings(pd: ProgData):

    update_set, test_set, add_set = update_test_add(pd.lookup_table, pd.spellings_dict)

    lookup_table_update_test = pd.db_session \
        .query(Lookup) \
        .filter(Lookup.lookup_key.in_(update_set)) \
        .all()
    
    print(f"[green]{'update_set':<30}", end="")

    # update test add
    if update_set:
        for i in lookup_table_update_test:
            if i.lookup_key in update_set:
                sorted_spelling = pali_list_sorter(pd.spellings_dict[i.lookup_key])
                i.spelling_pack(sorted_spelling)
            
            # test_set
            elif i.lookup_key in test_set:
                if is_another_value(i, "spelling"):
                    i.spelling = ""
                else:
                    pd.db_session.delete(i)    
    
    print(f"{len(update_set):>10,}")

    # add
    print(f"[green]{'add set':<30}", end="")

    if add_set:
        add_to_db = []
        for mistake, correction in pd.spellings_dict.items():
            if mistake in add_set:
                add_me = Lookup()
                add_me.lookup_key = mistake
                add_me.spelling_pack(pali_list_sorter(correction))
                add_to_db.append(add_me)

        pd.db_session.add_all(add_to_db)

    print(f"{len(add_set):>10,}")


def main():
    tic()
    print("[bright_yellow]add variants and spelling mistakes to lookup table")
    pd = ProgData()
    load_variant_dict(pd)
    add_variants(pd)
    load_spelling_dict(pd)
    add_spellings(pd)
    pd.db_session.commit()
    pd.db_session.close()
    toc()
    

if __name__ == "__main__":
    main()
