#!/usr/bin/env python3

import csv
import re
from typing import List
from pathlib import Path
from dpd.models import PaliWord, PaliRoot
from dpd.db_helpers import create_db_if_not_exists, get_db_session

dpd_db_path = Path("dpd.sqlite3")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()

def anki_row(i: PaliWord) -> List[str]:
    anki_fields = []

    anki_fields.extend([
        i.id,
        i.pali_1,
        i.pali_2,
    ])

    if i.sutta_1 != None and i.sutta_2 != None:
        sign = "√√"
    elif i.sutta_1 != None and i.sutta_2 == None:
        sign = "√"
    else:
        sign = ""

    anki_fields.append(sign)

    anki_fields.extend([
        i.pos,
        i.grammar,
        i.derived_from,
        i.neg,
        i.verb,
        i.trans,
        i.plus_case,
        i.meaning_1,
        i.meaning_lit,
        i.non_ia,
        i.sanskrit,
    ])

    if i.pali_root != None:
        anki_fields.extend([
            i.pali_root.sanskrit_root,
            i.pali_root.sanskrit_root_meaning,
            i.pali_root.sanskrit_root_class,
            re.sub(r' \d*$', '', str(i.root_key)),
            i.pali_root.root_in_comps,
            i.pali_root.root_has_verb,
            i.pali_root.root_group,
            i.root_sign,
            i.pali_root.root_meaning,
            i.pali_root.root_base,
        ])

    else:
        anki_fields.extend([
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ])

    anki_fields.extend([
        i.family_root,
        i.family_word,
        i.family_compound,
        i.construction,
        i.derivative,
        i.suffix,
        i.phonetic,
        i.compound_type,
        i.compound_construction,
        i.non_root_in_comps,
        i.source_1,
        i.sutta_1,
        i.example_1,
        i.source_2,
        i.sutta_2,
        i.example_2,
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary,
        i.notes,
        i.cognate,
        i.category,
        i.link,
        i.stem,
        i.pattern,
        i.meaning_2,
    ])

    return none_to_empty(anki_fields)

def vocab():
    # rows = []
    # for i in dpd_db:
    #     if i.meaning1 != None and i.example_1 != None:
    #         rows.append(anki_row(i))

    # The above loop can be written as:

    def _is_needed(i: PaliWord):
        return (i.meaning_1 != None and i.example_1 != None)

    # Using a list comprehension
    rows = [anki_row(i) for i in dpd_db if _is_needed(i)]

    # Using map(filter())
    # rows = list(map(anki_row, filter(_is_needed, dpd_db)))

    with open("csvs4anki/vocab.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

def commentary():
    rows = []
    for i in dpd_db:
        if i.meaning_1 != None and i.example_1 == None:
            rows.append(anki_row(i))

    with open("csvs4anki/commentary.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

def pass1():
    output_file = open("csvs4anki/pass1.csv", "w")

    rows = []
    for i in dpd_db:
        if i.meaning_1 == None and i.category != None and "pass1" in i.category:
            rows.append(anki_row(i))

    output_file.close()


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))

def main():
    vocab()
    commentary()
    pass1()

if __name__ == "__main__":
    main()
