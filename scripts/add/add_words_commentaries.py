#!/usr/bin/env python3

"""Find most common words in commentary without meaning"""

from collections import Counter
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.cst_sc_text_sets import make_cst_text_list
from tools.goldendict_tools import open_in_goldendict_os
from tools.pali_text_files import atthakatha_books, mula_books

def make_list_of_words_without_meaning(pth):
        
    db_session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = db_session.query(DpdHeadword).all()
    all_inflections_no_meanings_1 = set()
    all_inflection_with_meaning_1 = set()
    for counter, i in enumerate(db):
        if not i.meaning_1:
            for infl in i.inflections_list_all:
                all_inflections_no_meanings_1.add(infl)
        else:
            for infl in i.inflections_list_all:
                all_inflection_with_meaning_1.add(infl)

     
    print(len(all_inflections_no_meanings_1))
    print(len(all_inflection_with_meaning_1))
    return all_inflections_no_meanings_1, all_inflection_with_meaning_1
        

def make_list_of_all_words_in_book(pth, books):
    all_words_in_book = make_cst_text_list(
        pth,
        books,
        dedupe=False,
        add_hyphenated_parts=True)
    print(len(all_words_in_book))

    return all_words_in_book


def main():
    pth = ProjectPaths()
    atthakatha_books.remove("abha")
    # books = atthakatha_books
    books = [
    # "vin1", "vin2", "vin3", "vin4", "vin5",
    "dn1", "dn2", "dn3",
    "mn1", "mn2", "mn3",
    "sn1", "sn2", "sn3", "sn4", "sn5",
    "an1", "an2", "an3", "an4", "an5",
    "an6", "an7", "an8", "an9", "an10", "an11",
    # "kn1", "kn2", "kn3", "kn4", "kn5",
    # "kn6", "kn7", "kn8", "kn9", "kn10",
    # "kn11", "kn12", "kn13", "kn14", "kn15",
    # "kn16", "kn17", "kn18", "kn19", "kn20",
    ]

    (
        all_inflections_no_meanings_1,
        all_inflection_with_meaning_1
    ) = make_list_of_words_without_meaning(pth)
    
    list_of_all_words_in_book = make_list_of_all_words_in_book(pth, books)
    
    c = Counter(list_of_all_words_in_book)
    most_common = c.most_common()
    
    found_count = 0
    found_list = []
    for i in most_common:
        word, count = i
        if (
            word in all_inflections_no_meanings_1
            and word not in all_inflection_with_meaning_1
        ):
            found_count += 1
            found_list.append(f"[blue]{found_count}. {word}, {count}")

        if (
            word not in all_inflections_no_meanings_1
            and word not in all_inflection_with_meaning_1
        ):
            found_count += 1
            found_list.append(f"[red]{found_count}. {word}, {count}")
        
        if len(found_list) == 100:
            for f in found_list:
                print(f)
            found_list.clear()
            input()
            

if __name__ == "__main__":
    main()
