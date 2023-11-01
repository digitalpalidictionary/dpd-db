#!/usr/bin/env python3

"""Export db into dps related format: dpd_dps_full - full data of dpd + dps - for making full db with latest adding frequency in ebt column. So one can sort things abd find relevant data for class preparation. dps_full - only those part of data which have ru_meaning not empty.
also add sbs_index and sbs_audio based on some conditions"""

import csv
import re
import os
from rich.console import Console

from typing import List

from db.models import PaliWord
from db.get_db_session import get_db_session

from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths as DPSPTH
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.date_and_time import day

date = day()
console = Console()


def main():
    tic()
    console.print("[bold bright_yellow]exporting dps csvs")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()
    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.pali_1))

    dps(dpd_db)
    # full_db(dpd_db)
    
    toc()


def load_chant_index_map():
    """Load the chant-index mapping from a TSV file into a dictionary."""
    chant_index_map = {}
    with open(DPSPTH.sbs_index_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header row
        for row in reader:
            index, chant = row[0], row[1]
            chant_index_map[chant] = int(index)
    return chant_index_map


def load_chant_link_map():
    """Load the chant-link mapping from a TSV file into a dictionary."""
    chant_link_map = {}
    with open(DPSPTH.sbs_index_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header row
        for row in reader:
            chant, link = row[1], row[4]
            chant_link_map[chant] = link
    return chant_link_map


def load_class_link_map():
    """Load the class-link mapping from a TSV file into a dictionary."""
    class_link_map = {}
    with open(DPSPTH.class_index_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header row
        for row in reader:
            class_num, link = int(row[0]), row[2]  # Convert class_num to integer
            class_link_map[class_num] = link
    return class_link_map


def load_sutta_link_map():
    """Load the sutta-link mapping from a TSV file into a dictionary."""
    sutta_link_map = {}
    with open(DPSPTH.sutta_index_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header row
        for row in reader:
            sutta_num, link = row[0], row[2]
            sutta_link_map[sutta_num] = link
    return sutta_link_map




def dps(dpd_db):
    console.print("[bold green]making dps-full csv")

    def _is_needed(i: PaliWord):
        return (i.ru)

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
                    'meaning_2', 'sbs_index', 'sbs_audio', 'sbs_class', 'test', "sbs_link_1", "sbs_link_2", "sbs_link_3", "sbs_link_4", "class_link", "sutta_link"]
    
    rows = [header]  # Add the header as the first row
    rows.extend(pali_row(i) for i in dpd_db if _is_needed(i))

    with open(DPSPTH.dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    # dps_df = pd.read_csv(DPSPTH.dps_full_path, sep="\t", dtype=str)
    # dps_df.sort_values(
    #     by=["pali_1"], inplace=True, ignore_index=True,
    #     key=lambda x: x.map(pali_sort_key))
    # dps_df.to_csv(
    #     DPSPTH.dps_full_path, sep="\t", index=False,
    #     quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def pali_row(i: PaliWord, output="anki") -> List[str]:
    fields = []

    fields.extend([ 
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
    ])

    # Logic for sbs_index
    if i.sbs:
        chant_index_map = load_chant_index_map()

        chants = [i.sbs.sbs_chant_pali_1, i.sbs.sbs_chant_pali_2, i.sbs.sbs_chant_pali_3, i.sbs.sbs_chant_pali_4]

        indexes = [chant_index_map.get(chant) for chant in chants if chant in chant_index_map]

        if indexes:
            sbs_index = min(indexes)
        else:
            sbs_index = ""

        fields.append(sbs_index)

    # Logic for sbs_audio
    audio_path = os.path.join(DPSPTH.anki_media_dir, f"{i.pali_clean}.mp3")
    if os.path.exists(audio_path):
        sbs_audio = f"[sound:{i.pali_clean}.mp3]"
    else:
        sbs_audio = ''

    fields.append(sbs_audio)

    fields.extend([
        i.sbs.sbs_class if i.sbs else None,
        date
    ])
    # Logic for chant links
    if i.sbs:
        chant_link_map = load_chant_link_map()

        # Get the individual chants
        chants = [
            i.sbs.sbs_chant_pali_1,
            i.sbs.sbs_chant_pali_2,
            i.sbs.sbs_chant_pali_3,
            i.sbs.sbs_chant_pali_4
        ]

        # For each chant, get the corresponding link or an empty string if it doesn't exist
        links = [chant_link_map.get(chant, "") for chant in chants]

        # Append each link as separate fields
        fields.append(links[0])  # sbs_link_1
        fields.append(links[1])  # sbs_link_2
        fields.append(links[2])  # sbs_link_3
        fields.append(links[3])  # sbs_link_4

    # Logic for class links

    if i.sbs:
        # Call the function to get the mapping
        class_link_map = load_class_link_map()

        # Assuming you have an object `sbs` with an attribute `sbs_class_anki`
        class_num = i.sbs.sbs_class_anki

        # Assign the corresponding link from the map to class_link
        class_link = class_link_map.get(class_num, "")  # Default to empty string if the class number doesn't exist in the map

        fields.append(class_link)

    # Logic for sutta links

    if i.sbs:
        # Call the function to get the mapping
        sutta_link_map = load_sutta_link_map()

        # Assuming you have an object `sbs` with an attribute `sbs_category`
        sutta_num = i.sbs.sbs_category

        # Assign the corresponding link from the map to sutta_link
        sutta_link = sutta_link_map.get(sutta_num, "")  # Default to empty string if the sutta number doesn't exist in the map

        fields.append(sutta_link)

    

    return none_to_empty(fields)


def full_db(dpd_db):
    console.print("[bold green]making dpd-dps-full csv")
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
                    'meaning_2', 'sbs_index', 'sbs_audio', 'sbs_class', 'test', "sbs_link_1", "sbs_link_2", "sbs_link_3", "sbs_link_4", "class_link", "sutta_link"]

    rows.append(header)

    for i in dpd_db:
        rows.append(pali_row(i, output="dpd"))

    with open(DPSPTH.dpd_dps_full_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows)

    # full_df = pd.read_csv(DPSPTH.dpd_dps_full_path, sep="\t", dtype=str)
    # full_df.sort_values(
    #     by=["pali_1"], inplace=True, ignore_index=True,
    #     key=lambda x: x.map(pali_sort_key))
    # full_df.to_csv(
    #     DPSPTH.dpd_dps_full_path, sep="\t", index=False,
    #     quoting=csv.QUOTE_NONNUMERIC, quotechar='"')


def none_to_empty(values: List):
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


if __name__ == "__main__":
    main()
