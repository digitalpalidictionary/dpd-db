#!/usr/bin/env python3.11
# coding: utf-8

import csv
import re
import pandas as pd

from tqdm import tqdm
from typing import List
from pathlib import Path
from tools.sorter import sort_key

from db.models import PaliWord, PaliRoot
from db.get_db_session import get_db_session

dpd_db_path = Path("dpd.db")
db_session = get_db_session(dpd_db_path)
dpd_db = db_session.query(PaliWord).all()
roots_db = db_session.query(PaliRoot).all()


def pali_row(i: PaliWord, output="anki") -> List[str]:
    fields = []

    fields.extend([
        i.user_id,
        i.pali_1,
        i.pali_2,
    ])

    if i.sutta_1 != "" and i.sutta_2 != "":
        sign = "√√"
    elif i.sutta_1 != "" and i.sutta_2 == "":
        sign = "√"
    else:
        sign = ""

    fields.append(sign)

    fields.extend([
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

    if i.pali_root is not None:
        if output == "dpd":
            root_key = i.root_key
            if i.pali_root.root_in_comps == "":
                root_in_comps = "0"
            else:
                root_in_comps = i.pali_root.root_in_comps

            if i.pali_root.sanskrit_root_meaning == "":
                sanskrit_root_meaning = "0"
            else:
                sanskrit_root_meaning = i.pali_root.sanskrit_root_meaning

        else:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
            root_in_comps = i.pali_root.root_in_comps
            sanskrit_root_meaning = i.pali_root.sanskrit_root_meaning

        fields.extend([
            i.pali_root.sanskrit_root,
            sanskrit_root_meaning,
            i.pali_root.sanskrit_root_class,
            root_key,
            root_in_comps,
            i.pali_root.root_has_verb,
            i.pali_root.root_group,
            i.root_sign,
            i.pali_root.root_meaning,
            i.root_base,
        ])

    else:
        fields.extend([
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

    fields.extend([
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
        i.family_set,
        i.link,
        i.stem,
        i.pattern,
        i.meaning_2,
    ])

    return none_to_empty(fields)


def vocab():

    def _is_needed(i: PaliWord):
        return (i.meaning_1 != "" and i.example_1 != "")

    rows = [pali_row(i) for i in dpd_db if _is_needed(i)]

    with open("csvs/vocab.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def commentary():
    print("making commentary csv")
    rows = []

    for i in tqdm(dpd_db):
        if i.meaning_1 != "" and i.example_1 == "":
            rows.append(pali_row(i))

    with open("csvs/commentary.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def pass1():
    print("making pass1 csv")
    output_file = open("csvs/pass1.csv", "w")

    rows = []
    for i in tqdm(dpd_db):
        if i.meaning_1 == "" and i.family_set != "" and "pass1" in i.family_set:
            rows.append(pali_row(i))

    output_file.close()


def full_db():
    print("making dpd-full csv")
    rows = []
    header = ['ID', 'Pāli1', 'Pāli2', 'Fin', 'POS', 'Grammar', 'Derived from',
                    'Neg', 'Verb', 'Trans', 'Case', 'Meaning IN CONTEXT',
                    'Literal Meaning', 'Non IA', 'Sanskrit', 'Sk Root',
                    'Sk Root Mn', 'Cl', 'Pāli Root', 'Root In Comps', 'V',
                    'Grp', 'Sgn', 'Root Meaning', 'Base', 'Family',
                    'Word Family', 'Family2', 'Construction', 'Derivative',
                    'Suffix', 'Phonetic Changes', 'Compound',
                    'Compound Construction', 'Non-Root In Comps', 'Source1',
                    'Sutta1', 'Example1', 'Source 2', 'Sutta2', 'Example 2',
                    'Antonyms', 'Synonyms – different word',
                    'Variant – same constr or diff reading',  'Commentary',
                    'Notes', 'Cognate', 'Category', 'Link', 'Stem', 'Pattern',
                    'Buddhadatta']

    rows.append(header)

    for i in tqdm(dpd_db):
        rows.append(pali_row(i, output="dpd"))

    with open("csvs/dpd-full.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    dpd_df = pd.read_csv("csvs/dpd-full.csv", sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["Pāli1"], inplace=True, ignore_index=True,
        key=lambda x: x.map(sort_key))
    dpd_df.to_csv(
        "csvs/dpd-full.csv", sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def roots():

    print("making roots list")
    roots_list = []
    for i in tqdm(roots_db):
        roots_list += [i.root]

    print("making roots count dictionary")
    root_count_dict = {}
    for root in tqdm(roots_list):
        count = db_session.query(PaliWord).filter(
            PaliWord.root_key == root).count()
        root_count_dict[root] = count

    print("making roots.csv")
    rows = []
    roots_header = [
        "Fin", "Count", "Root", "In Comps", "V", "Group", "Sign",
        "Base", "Meaning", "Sk Root", "Sk Root Mn", "Cl", "Example",
        "Dhātupātha", "DpRoot", "DpPāli", "DpEnglish",
        "Kaccāyana Dhātu Mañjūsā", "DmRoot", "DmPāli", "DmEnglish",
        "Saddanītippakaraṇaṃ Dhātumālā", "SnPāli", "SnEnglish",
        "Pāṇinīya Dhātupāṭha", "PdSanskrit", "PdEnglish", "Note",
        "Padaūpasiddhi", "PrPāli", "PrEnglish", "blanks", "same/diff",
        "matrix test"]

    rows.append(roots_header)

    for i in tqdm(roots_db):
        rows.append(root_row(i, root_count_dict))

    with open("csvs/roots.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(rows)

    dpd_df = pd.read_csv("csvs/roots.csv", sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["Root"], inplace=True, ignore_index=True,
        key=lambda x: x.map(sort_key))
    dpd_df.to_csv(
        "csvs/roots.csv", sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def root_row(i: PaliRoot, root_count_dict: dict) -> List[str]:
    root_fields = []

    root_fields.extend([
        "",
        root_count_dict[i.root],
        i.root,
        i.root_in_comps,
        i.root_has_verb,
        i.root_group,
        i.root_sign,
        "",     # base
        i.root_meaning,
        i.sanskrit_root,
        i.sanskrit_root_meaning,
        i.sanskrit_root_class,
        i.root_example,
        i.dhatupatha_num,
        i.dhatupatha_root,
        i.dhatupatha_pali,
        i.dhatupatha_english,
        i.dhatumanjusa_num,
        i.dhatumanjusa_root,
        i.dhatumanjusa_pali,
        i.dhatumanjusa_english,
        i.dhatumala_root,
        i.dhatumala_pali,
        i.dhatumala_english,
        i.panini_root,
        i.panini_sanskrit,
        i.panini_english,
        i.note,
        "",     # rupasiddhi
        "",
        "",
        "",     # blanks
        "",     # same/diff
        i.matrix_test
    ])

    return none_to_empty(root_fields)


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


def export_anki_csvs():
    vocab()
    commentary()
    pass1()
    full_db()
    roots()


def main():
    export_anki_csvs()


if __name__ == "__main__":
    main()
