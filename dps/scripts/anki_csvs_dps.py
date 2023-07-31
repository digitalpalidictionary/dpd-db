#!/usr/bin/env python3

"""Export db into dps related format: dpd_dps_full - fulla data of dpd + dps - for making full db with latest adding frequency in ebt column. So one can sort things abd find relevant data for class preparation. dps_full - only those part of data which have ru_meaning nit empty. from this file can be filterd csv for various anki decks related to pali class and SBS recitation book"""

import csv
import re
import pandas as pd
from rich import print

from typing import List

from db.models import PaliWord
from db.get_db_session import get_db_session

from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths as PTHDPS
from tools.paths import ProjectPaths as PTH
from tools.tic_toc import tic, toc
# from tools.tsv_read_write import write_tsv_list
from tools.date_and_time import day

date = day()


def main():
    tic()
    print("[bright_yellow]exporting dps csvs")

    db_session = get_db_session(PTH.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    dps(dpd_db)
    # full_db(dpd_db)
    
    toc()


def dps(dpd_db):
    print("[green]making dps-full csv")

    def _is_needed(i: PaliWord):
        return (i.ru)

    header = ['user_id', 'id', 'pali_1', 'pali_2', 'fin', 'sbs_class_anki', 'sbs_category', 'pos', 'grammar', 'derived_from',
                    'neg', 'verb', 'trans', 'plus_case', 'meaning_1',
                    'meaning_lit', 'ru_meaning', 'ru_meaning_lit', 'sbs_meaning', 'non_ia', 'sanskrit', 'sanskrit_root',
                    'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_in_comps', 'root_has_verb',
                    'root_group', 'root_sign', 'root_meaning', 'root_base', 'family_root',
                    'family_word', 'family_compound', 'construction', 'derivative',
                    'suffix', 'phonetic', 'compound_type',
                    'compound_construction', 'non_root_in_comps', 'source_1',
                    'sutta_1', 'example_1', 'source_2', 'sutta_2', 'example_2',
                    'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1',
                    'sbs_source_2', 'sbs_sutta_2', 'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2',
                    'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4',
                    'antonym', 'synonym',
                    'variant',  'commentary',
                    'notes', 'sbs_notes', 'ru_notes', 'cognate', 'family_set', 'link', 'stem', 'pattern',
                    'meaning_2', 'sbs_index', 'sbs_audio', 'sbs_class', 'test']
    
    rows = [header]  # Add the header as the first row
    rows.extend(pali_row(i) for i in dpd_db if _is_needed(i))

    with open(PTHDPS.dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    dpd_df = pd.read_csv(PTHDPS.dps_full_path, sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["pali_1"], inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))
    dpd_df.to_csv(
        PTHDPS.dps_full_path, sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def pali_row(i: PaliWord, output="anki") -> List[str]:
    fields = []

    fields.extend([
        i.user_id,  
        i.id,
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
        i.construction.replace("\n", "<br>"),
        i.derivative,
        i.suffix,
        i.phonetic.replace("\n", "<br>"),
        i.compound_type,
        i.compound_construction,
        i.non_root_in_comps,
        i.source_1.replace("\n", "<br>"),
        i.sutta_1.replace("\n", "<br>"),
        i.example_1.replace("\n", "<br>"),
        i.source_2.replace("\n", "<br>"),
        i.sutta_2.replace("\n", "<br>"),
        i.example_2.replace("\n", "<br>"),
        i.sbs.sbs_source_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_chant_pali_1 if i.sbs else None,
        i.sbs.sbs_chant_eng_1 if i.sbs else None,
        i.sbs.sbs_chapter_1 if i.sbs else None,
        i.sbs.sbs_source_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_chant_pali_2 if i.sbs else None,
        i.sbs.sbs_chant_eng_2 if i.sbs else None,
        i.sbs.sbs_chapter_2 if i.sbs else None,
        i.sbs.sbs_source_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_chant_pali_3 if i.sbs else None,
        i.sbs.sbs_chant_eng_3 if i.sbs else None,
        i.sbs.sbs_chapter_3 if i.sbs else None,  
        i.sbs.sbs_source_4.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_4.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_4.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_chant_pali_4 if i.sbs else None,
        i.sbs.sbs_chant_eng_4 if i.sbs else None,
        i.sbs.sbs_chapter_4 if i.sbs else None, 
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary.replace("\n", "<br>"),
        i.notes.replace("\n", "<br>"),
        i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
        i.ru.ru_notes.replace("\n", "<br>") if i.ru else None,
        i.cognate,
        i.family_set,
        i.link.replace("\n", "<br>"),
        i.stem,
        i.pattern,
        i.meaning_2,
        i.sbs.sbs_index if i.sbs else None,      
        i.sbs.sbs_audio if i.sbs else None, 
        i.sbs.sbs_class if i.sbs else None,
        date 

    ])

    return none_to_empty(fields)


def full_db(dpd_db):
    print("[green]making dpd-dps-full csv")
    rows = []
    header = ['id', 'pali_1', 'pali_2', 'fin', 'sbs_class_anki', 'sbs_category', 'pos', 'grammar', 'derived_from',
                    'neg', 'verb', 'trans', 'plus_case', 'meaning_1',
                    'meaning_lit', 'ru_meaning', 'ru_meaning_lit', 'sbs_meaning', 'non_ia', 'sanskrit', 'sanskrit_root',
                    'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_in_comps', 'root_has_verb',
                    'root_group', 'root_sign', 'root_meaning', 'root_base', 'family_root',
                    'family_word', 'family_compound', 'construction', 'derivative',
                    'suffix', 'phonetic', 'compound_type',
                    'compound_construction', 'non_root_in_comps', 'source_1',
                    'sutta_1', 'example_1', 'source_2', 'sutta_2', 'example_2',
                    'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1',
                    'sbs_source_2', 'sbs_sutta_2', 'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2',
                    'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4',
                    'antonym', 'synonym',
                    'variant',  'commentary',
                    'notes', 'sbs_notes', 'ru_notes', 'cognate', 'family_set', 'link', 'stem', 'pattern',
                    'meaning_2', 'sbs_index', 'sbs_audio', 'sbs_class', 'test']

    rows.append(header)

    for i in dpd_db:
        rows.append(pali_row(i, output="dpd"))

    with open(PTHDPS.dpd_dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    dpd_df = pd.read_csv(PTHDPS.dpd_dps_full_path, sep="\t", dtype=str)
    dpd_df.sort_values(
        by=["pali_1"], inplace=True, ignore_index=True,
        key=lambda x: x.map(pali_sort_key))
    dpd_df.to_csv(
        PTHDPS.dpd_dps_full_path, sep="\t", index=False,
        quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main()
