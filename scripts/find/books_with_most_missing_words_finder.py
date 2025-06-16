#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Find which books have the most missing words"""

import json
from collections import defaultdict
from typing import Counter

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.pali_text_files import cst_texts
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    example_true = set()
    example_false = set()

    for counter, i in enumerate(db):
        if i.example_1 and i.meaning_1:
            example_true.update(set(i.inflections_list_all))
        elif not i.example_1:
            example_false.update(set(i.inflections_list_all))
        else:
            print(i.lemma_1)

    example_false = example_false - example_true

    with open(pth.cst_file_freq) as f:
        cst_file_freq = json.load(f)

    books_counter_freq = Counter()
    books_counter_words = Counter()

    for file, data in cst_file_freq.items():
        books_counter_freq[file] = 0
        for word, freq in data.items():
            if word in example_false:
                books_counter_freq[file] += freq
                books_counter_words[file] += 1

    sorted_freq = books_counter_freq.most_common()
    sorted_words = books_counter_words.most_common()

    # invert cst_texts
    cst_book = {}
    for book, files in cst_texts.items():
        for file in files:
            file = file.replace(".txt", ".xml")
            cst_book[file] = book

    print("frequency in books")
    for file, count in sorted_freq:
        if "mul" in file and (file.startswith("s") or file.startswith("vin")):
            print(f"{cst_book[file]:<10}: {count}")

    print()
    print("count in books")
    for file, count in sorted_words:
        if "mul" in file and (file.startswith("s") or file.startswith("vin")):
            print(f"{cst_book[file]:<10}: {count}")

    print()
    print("word frequency in books")
    freq_dict = Counter()
    for file, count in sorted_freq:
        if "mul" in file and (file.startswith("s") or file.startswith("vin")):
            if file.startswith("s01"):
                freq_dict["dn"] += count
            elif file.startswith("s02"):
                freq_dict["mn"] += count
            elif file.startswith("s03"):
                freq_dict["sn"] += count
            elif file.startswith("s04"):
                freq_dict["an"] += count
            elif file.startswith("s05"):
                freq_dict["kn"] += count
            elif file.startswith("vin"):
                freq_dict["vin"] += count
    print(freq_dict.most_common())

    print()
    print("word count in books")
    freq_dict = Counter()
    for file, count in sorted_words:
        if "mul" in file and (file.startswith("s") or file.startswith("vin")):
            if file.startswith("s01"):
                freq_dict["dn"] += count
            elif file.startswith("s02"):
                freq_dict["mn"] += count
            elif file.startswith("s03"):
                freq_dict["sn"] += count
            elif file.startswith("s04"):
                freq_dict["an"] += count
            elif file.startswith("s05"):
                freq_dict["kn"] += count
            elif file.startswith("vin"):
                freq_dict["vin"] += count
    print(freq_dict.most_common())


if __name__ == "__main__":
    main()
