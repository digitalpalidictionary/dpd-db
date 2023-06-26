#!/usr/bin/env python3.11

import csv
import re
import pandas as pd
from rich import print

from typing import List

from db.models import PaliWord, PaliRoot
from db.get_db_session import get_db_session

from tools.pali_sort_key import pali_sort_key
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH


def main():
    tic()
    print("[bright_yellow]exporting anki csv")

    db_session = get_db_session("dpd.db")
    dpd_db = db_session.query(PaliWord).all()
    roots_db = db_session.query(PaliRoot).all()

    # vocab(dpd_db)
    # commentary(dpd_db)
    # pass1(dpd_db)
    full_db(dpd_db)
    # roots(db_session, roots_db)

    toc()


# def vocab(dpd_db):

#     def _is_needed(i: PaliWord):
#         return (i.meaning_1 != "" and i.example_1 != "")

#     rows = [pali_row(i) for i in dpd_db if _is_needed(i)]

#     with open(PTH.vocab_csv_path, "w", newline='', encoding='utf-8') as f:
#         writer = csv.writer(f, delimiter='\t')
#         writer.writerows(rows)


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
        i.sbs.sbs_class_anki if i.sbs else None, 
        i.sbs.sbs_category if i.sbs else None, 
        i.pos,
        i.grammar,
        i.derived_from,
        i.neg,
        i.verb,
        i.trans,
        i.plus_case,
        i.meaning_1,
        i.meaning_lit,
        i.ru.ru_meaning if i.ru else None,
        i.ru.ru_meaning_lit if i.ru else None,
        i.sbs.sbs_meaning if i.sbs else None,  
        i.non_ia,
        i.sanskrit,
    ])

    if i.rt is not None:
        if output == "dpd":
            root_key = i.root_key
            if i.rt.root_in_comps == "":
                root_in_comps = "0"
            else:
                root_in_comps = i.rt.root_in_comps

            if i.rt.sanskrit_root_meaning == "":
                sanskrit_root_meaning = "0"
            else:
                sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        else:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
            root_in_comps = i.rt.root_in_comps
            sanskrit_root_meaning = i.rt.sanskrit_root_meaning

        fields.extend([
            i.rt.sanskrit_root,
            sanskrit_root_meaning,
            i.rt.sanskrit_root_class,
            root_key,
            root_in_comps,
            i.rt.root_has_verb,
            i.rt.root_group,
            i.root_sign,
            i.rt.root_meaning,
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
        i.sbs.sbs_chant_pali_1 if i.sbs else None,
        i.sbs.sbs_chant_eng_1 if i.sbs else None,
        i.sbs.sbs_chapter_1 if i.sbs else None,
        i.source_2,
        i.sutta_2,
        i.example_2,
        i.sbs.sbs_chant_pali_2 if i.sbs else None,
        i.sbs.sbs_chant_eng_2 if i.sbs else None,
        i.sbs.sbs_chapter_2 if i.sbs else None,
        i.sbs.sbs_source_3 if i.sbs else None,
        i.sbs.sbs_sutta_3 if i.sbs else None,
        i.sbs.sbs_example_3 if i.sbs else None,
        i.sbs.sbs_chant_pali_3 if i.sbs else None,
        i.sbs.sbs_chant_eng_3 if i.sbs else None,
        i.sbs.sbs_chapter_3 if i.sbs else None,  
        i.sbs.sbs_source_4 if i.sbs else None,
        i.sbs.sbs_sutta_4 if i.sbs else None,
        i.sbs.sbs_example_4 if i.sbs else None,
        i.sbs.sbs_chant_pali_4 if i.sbs else None,
        i.sbs.sbs_chant_eng_4 if i.sbs else None,
        i.sbs.sbs_chapter_4 if i.sbs else None, 
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary,
        i.notes,
        i.sbs.sbs_notes if i.sbs else None,
        i.ru.ru_notes if i.ru else None,
        i.cognate,
        i.family_set,
        i.link,
        i.stem,
        i.pattern,
        i.meaning_2,
        i.sbs.sbs_index if i.sbs else None,      
        i.sbs.sbs_audio if i.sbs else None, 
        i.sbs.sbs_class if i.sbs else None, 

    ])

    return none_to_empty(fields)


# def commentary(dpd_db):
#     print("[green]making commentary csv")
#     rows = []

#     for i in dpd_db:
#         if i.meaning_1 != "" and i.example_1 == "":
#             rows.append(pali_row(i))

#     with open(PTH.commentary_csv_path, "w", newline='', encoding='utf-8') as f:
#         writer = csv.writer(f, delimiter='\t')
#         writer.writerows(rows)


# def pass1(dpd_db):
#     print("[green]making pass1 csv")
#     output_file = open(PTH.pass1_csv_path, "w")

#     rows = []
#     for i in dpd_db:
#         if i.meaning_1 == "" and i.family_set != "" and "pass1" in i.family_set:
#             rows.append(pali_row(i))

#     output_file.close()


def full_db(dpd_db):
    print("[green]making dpd-dps-full csv")
    rows = []
    header = ['id', 'pali_1', 'pali_2', 'Fin', 'sbs_class_anki', 'sbs_category', 'pos', 'grammar', 'derived_from',
                    'neg', 'verb', 'trans', 'plus_case', 'meaning_1',
                    'meaning_lit', 'ru_meaning', 'ru_meaning_lit', 'sbs_meaning', 'Non IA', 'sanskrit', 'root_sk',
                    'Sk Root Mn', 'Cl', 'root_pali', 'Root In Comps', 'V',
                    'Grp', 'Sgn', 'Root Meaning', 'root_base', 'Family',
                    'Word Family', 'Family2', 'construction', 'derivative',
                    'suffix', 'phonetic', 'compound_type',
                    'compound_construction', 'Non-Root In Comps', 'source_1',
                    'sutta_1', 'example_1', 'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1',
                    'source_2', 'sutta_2', 'example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2',
                    'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4',
                    'Antonyms', 'Synonyms – different word',
                    'variant',  'commentary',
                    'notes', 'sbs_notes', 'ru_notes', 'Cognate', 'Category', 'Link', 'stem', 'pattern',
                    'Buddhadatta', 'sbs_index', 'sbs_audio', 'sbs_class']

    rows.append(header)

    for i in dpd_db:
        rows.append(pali_row(i, output="dpd"))

    with open(PTH.dpd_dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    dpd_df = pd.read_csv(PTH.dpd_dps_full_path, sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["pali_1"], inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))
    dpd_df.to_csv(
        PTH.dpd_dps_full_path, sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


# def roots(db_session, roots_db):

#     print("[green]making roots list")
#     roots_list = []
#     for i in roots_db:
#         roots_list += [i.root]

#     print("[green]making roots count dictionary")
#     root_count_dict = {}
#     for root in roots_list:
#         count = db_session.query(PaliWord).filter(
#             PaliWord.root_key == root).count()
#         root_count_dict[root] = count

#     print("[green]making roots.csv")
#     rows = []
#     roots_header = [
#         "Fin", "Count", "Root", "In Comps", "V", "Group", "Sign",
#         "Base", "Meaning", "Sk Root", "Sk Root Mn", "Cl", "Example",
#         "Dhātupātha", "DpRoot", "DpPāli", "DpEnglish",
#         "Kaccāyana Dhātu Mañjūsā", "DmRoot", "DmPāli", "DmEnglish",
#         "Saddanītippakaraṇaṃ Dhātumālā", "SnPāli", "SnEnglish",
#         "Pāṇinīya Dhātupāṭha", "PdSanskrit", "PdEnglish", "Note",
#         "Padaūpasiddhi", "PrPāli", "PrEnglish", "blanks", "same/diff",
#         "matrix test"]

#     rows.append(roots_header)

#     for i in roots_db:
#         rows.append(root_row(i, root_count_dict))

#     with open(PTH.roots_csv_path, "w", newline='', encoding='utf-8') as f:
#         writer = csv.writer(f, delimiter="\t")
#         writer.writerows(rows)

#     dpd_df = pd.read_csv(PTH.roots_csv_path, sep="\t", dtype=str)
#     dpd_df.sort_values(
#         by=["Root"], inplace=True, ignore_index=True,
#         key=lambda x: x.map(pali_sort_key))
#     dpd_df.to_csv(
#         PTH.roots_csv_path, sep="\t", index=False,
#         quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


# def root_row(i: PaliRoot, root_count_dict: dict) -> List[str]:
#     root_fields = []

#     root_fields.extend([
#         "",
#         root_count_dict[i.root],
#         i.root,
#         i.root_in_comps,
#         i.root_has_verb,
#         i.root_group,
#         i.root_sign,
#         "",     # base
#         i.root_meaning,
#         i.sanskrit_root,
#         i.sanskrit_root_meaning,
#         i.sanskrit_root_class,
#         i.root_example,
#         i.dhatupatha_num,
#         i.dhatupatha_root,
#         i.dhatupatha_pali,
#         i.dhatupatha_english,
#         i.dhatumanjusa_num,
#         i.dhatumanjusa_root,
#         i.dhatumanjusa_pali,
#         i.dhatumanjusa_english,
#         i.dhatumala_root,
#         i.dhatumala_pali,
#         i.dhatumala_english,
#         i.panini_root,
#         i.panini_sanskrit,
#         i.panini_english,
#         i.note,
#         "",     # rupasiddhi
#         "",
#         "",
#         "",     # blanks
#         "",     # same/diff
#         i.matrix_test
#     ])

#     return none_to_empty(root_fields)


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main()
