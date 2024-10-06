#!/usr/bin/env python3

"""Export db into dps related format: dpd_dps_full - full data of dpd + dps - for making full db with latest adding frequency in ebt column. So one can sort things abd find relevant data for class preparation. dps_full - only those part of data which have ru_meaning not empty.
also add sbs_index and sbs_audio based on some conditions"""

import csv
import re
from rich.console import Console

from typing import List

from db.models import DpdHeadword
from db.db_helpers import get_db_session

from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
import datetime

from sqlalchemy.orm import joinedload

from dps.tools.sbs_table_functions import SBS_table_tools

current_date = datetime.date.today().strftime("%d-%m-%y")

console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]exporting dps csvs")

    pth = ProjectPaths()
    dpspth = DPSPaths()

    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.lemma_1))

    dps(dpspth, dpd_db)
    toc()
    
    # full_db(dpspth, dpd_db)
    

def get_header():
    return [
        'id', 'pali_1', 'pali_2', 'fin', 'sbs_class_anki', 'sbs_category', 'sbs_class', 'pos', 'grammar', 'derived_from',
        'neg', 'verb', 'trans', 'plus_case', 'meaning_1',
        'meaning_lit', 'ru_meaning', 'ru_meaning_lit', 'sbs_meaning', 'non_ia', 'sanskrit', 'sanskrit_root',
        'sanskrit_root_meaning', 'sanskrit_root_class', 'sanskrit_root_ru_meaning', 'root', 'root_in_comps', 'root_has_verb',
        'root_group', 'root_sign', 'root_meaning', 'root_ru_meaning', 'root_base', 'family_root',
        'family_word', 'family_compound', 'construction', 'derivative',
        'suffix', 'phonetic', 'compound_type',
        'compound_construction', 'non_root_in_comps', 'source_1',
        'sutta_1', 'example_1', 'source_2', 'sutta_2', 'example_2',
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1',
        'sbs_source_2', 'sbs_sutta_2', 'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2',
        'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 
        'sbs_source_4', 'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4',
        'antonym', 'synonym',
        'variant', 'commentary',
        'notes', 'sbs_notes', 'ru_notes', 'cognate', 'family_set', 'link', 'stem', 'pattern',
        'meaning_2', 'test', 'sbs_index', 'sbs_audio', 
        "sbs_link_1", "sbs_link_2", "sbs_link_3", "sbs_link_4", "class_link", "sutta_link"
    ]


def dps(dpspth, dpd_db):
    console.print("[bold green]making dps-full csv")

    def _is_needed(i: DpdHeadword):
        return (i.ru)

    header = get_header()   
    rows = [header]  # Add the header as the first row
    rows.extend(pali_row(dpspth, i) for i in dpd_db if _is_needed(i))

    num_rows = len(rows)  # Count the number of rows before writing to the file
    console.print(f"Number of rows: [bold]{num_rows}[/bold]")

    with open(dpspth.dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)


def pali_row(dpspth, i: DpdHeadword, output="anki") -> List[str]:
    fields = []

    fields.extend([ 
        i.id,
        i.lemma_1,
        i.lemma_2,
    ])

    if i.sutta_1 and i.sutta_2:
        sign = "√√"
    elif i.sutta_1 and not i.sutta_2:
        sign = "√"
    else:
        sign = ""

    fields.append(sign)

    fields.extend([
        i.sbs.sbs_class_anki if i.sbs else None, 
        i.sbs.sbs_category if i.sbs else None,
        i.sbs.sbs_class if i.sbs else None,
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
            if not i.rt.root_in_comps:
                root_in_comps = "0"
            else:
                root_in_comps = i.rt.root_in_comps

            if not i.rt.sanskrit_root_meaning:
                sanskrit_root_meaning = "0"
                sanskrit_root_ru_meaning = "0"
            else:
                sanskrit_root_meaning = i.rt.sanskrit_root_meaning
                sanskrit_root_ru_meaning = i.rt.sanskrit_root_ru_meaning

        else:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
            root_in_comps = i.rt.root_in_comps
            sanskrit_root_meaning = i.rt.sanskrit_root_meaning
            sanskrit_root_ru_meaning = i.rt.sanskrit_root_ru_meaning

        fields.extend([
            i.rt.sanskrit_root,
            sanskrit_root_meaning,
            sanskrit_root_ru_meaning,
            i.rt.sanskrit_root_class,
            root_key,
            root_in_comps,
            i.rt.root_has_verb,
            i.rt.root_group,
            i.root_sign,
            i.rt.root_meaning,
            i.rt.root_ru_meaning,
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
            "",
            "",
        ])

    fields.extend([
        i.family_root,
        i.family_word,
        i.family_compound,
        i.construction.replace("\n", "<br>") if i.construction else None,
        i.derivative,
        i.suffix,
        i.phonetic.replace("\n", "<br>") if i.phonetic else None,
        i.compound_type,
        i.compound_construction,
        i.non_root_in_comps,
        i.source_1.replace("\n", "<br>") if i.source_1 else None,
        i.sutta_1.replace("\n", "<br>") if i.sutta_1 else None,
        i.example_1.replace("\n", "<br>") if i.example_1 else None,
        i.source_2.replace("\n", "<br>") if i.source_2 else None,
        i.sutta_2.replace("\n", "<br>") if i.sutta_2 else None,
        i.example_2.replace("\n", "<br>") if i.example_2 else None,
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
        i.commentary.replace("\n", "<br>") if i.commentary else None,
        i.notes.replace("\n", "<br>") if i.notes else None,
        i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
        i.ru.ru_notes.replace("\n", "<br>") if i.ru else None,
        i.cognate,
        i.family_set,
        i.link.replace("\n", "<br>") if i.link else None,
        i.stem,
        i.pattern,
        i.meaning_2,
        current_date,
        i.sbs.sbs_index if i.sbs else None
    ])

    # sbs_audio
    fields.append(SBS_table_tools().generate_sbs_audio(i.lemma_clean))

    fields.extend([
        i.sbs.sbs_chant_link_1 if i.sbs else None,
        i.sbs.sbs_chant_link_2 if i.sbs else None,
        i.sbs.sbs_chant_link_3 if i.sbs else None,
        i.sbs.sbs_chant_link_4 if i.sbs else None,
        i.sbs.sbs_class_link if i.sbs else None,
        i.sbs.sbs_sutta_link if i.sbs else None,
    ])

    return none_to_empty(fields)


def full_db(dpspth, dpd_db):
    tic()
    console.print("[bold green]making dpd-dps-full csv")
    rows = []
    header = get_header()
    rows.append(header)

    for i in dpd_db:
        rows.append(pali_row(dpspth, i, output="dpd"))

    num_rows = len(rows)  # Count the number of rows before writing to the file
    console.print(f"Number of rows: [bold]{num_rows}[/bold]")

    with open(dpspth.dpd_dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    toc()


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main()
