#!/usr/bin/env python3

"""
Export db into csv for various anki decks
- dhp
- sbs ped
- parittas
- dps
- pali classes
- suttas
- roots and phonetic changes for pali class
- vibhanga for bhikkhu patimokkha

"""

import csv
import re
import os
from rich.console import Console

from typing import List

from db.models import DpdHeadword, SBS
from db.db_helpers import get_db_session

from tools.pali_sort_key import pali_sort_key
from dps.tools.paths_dps import DPSPaths
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
import datetime

from sqlalchemy.orm import joinedload

from dps.tools.sbs_table_functions import SBS_table_tools

current_date = datetime.date.today().strftime("%d-%m")

console = Console()

sbs_ped_link = 'Spot a mistake? <a class="link" href="https://docs.google.com/forms/d/e/1FAIpQLScNC5v2gQbBCM3giXfYIib9zrp-WMzwJuf_iVXEMX2re4BFFw/viewform?usp=pp_url&entry.438735500'

dps_link = 'Нашли ошибку? <a class="link" href="https://docs.google.com/forms/d/1iMD9sCSWFfJAFCFYuG9HRIyrr9KFRy0nAOVApM998wM/viewform?usp=pp_url&entry.438735500'


def join(*args):
    """Join elements of a list with a specified separator."""
    return ' '.join(filter(None, [arg.replace(" ", "-") if arg else None for arg in args]))


def none_to_empty(values: List):
    """Replace None with empty string."""
    def _to_empty(x):
        if x is None:
            return ""
        else:
            return x

    return list(map(_to_empty, values))


def get_feedback(i: DpdHeadword, deck_name):
    """Get the feedback link for a given deck."""
    if deck_name == "dps":
        return f"""{dps_link}={i.lemma_1}&entry.1433863141={deck_name.upper()}-{current_date}">Пожалуйста сообщите.</a>"""
    else:
        return f"""{sbs_ped_link}={i.lemma_1}&entry.1433863141={deck_name.upper()}-{current_date}">Fix it here.</a>"""


def get_root_info(i: DpdHeadword):
    """Get all root data with keys from a DpdHeadword object."""
    if i.rt is not None:
        root_key = re.sub(r" \d*$", "", str(i.root_key))

    return [
        i.rt.sanskrit_root if i.rt else None,
        i.rt.sanskrit_root_meaning if i.rt else None,
        i.rt.sanskrit_root_class if i.rt else None,
        root_key if i.rt else None,
        i.rt.root_has_verb if i.rt else None,
        i.rt.root_group if i.rt else None,
        i.root_sign if i.rt else None,
        i.rt.root_meaning if i.rt else None,
        i.root_base if i.rt else None,
    ]


def get_grammar_and_meaning(i: DpdHeadword):
    """Get all grammar data with meanings from a DpdHeadword object."""
    grammar_and_meaning = [
        i.grammar,
        i.neg,
        i.verb,
        i.trans,
        i.plus_case,
        i.meaning_1 if i.meaning_1 else i.meaning_2,
        i.meaning_lit,
    ]

    return grammar_and_meaning


def get_construction(i):
    """Get all construction data from a DpdHeadword object."""
    construction = [
        i.construction.replace("\n", "<br>") if i.construction else None,
        i.derivative,
        i.suffix,
        i.phonetic.replace("\n", "<br>") if i.phonetic else None,
        i.compound_type,
        i.compound_construction,
    ]

    return construction


def get_sbs_info(i: DpdHeadword):
    """Get all SBS related data from a DpdHeadword object."""
    sbs_info = [
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
    ]

    return sbs_info


def get_examples(i: DpdHeadword):
    """Get all examples info from a DpdHeadword object."""
    examples_info = [
        i.sbs.sbs_source_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_1.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_source_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_2.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_source_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_3.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_source_4.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_sutta_4.replace("\n", "<br>") if i.sbs else None,
        i.sbs.sbs_example_4.replace("\n", "<br>") if i.sbs else None,
        i.antonym,
        i.synonym,
        i.variant,
        i.commentary.replace("\n", "<br>") if i.commentary else None,
        i.notes.replace("\n", "<br>") if i.notes else None,
        i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
        i.link.replace("\n", "<br>") if i.link else None,
    ]

    # sbs_audio
    examples_info.append(SBS_table_tools().generate_sbs_audio(i.lemma_clean))

    return examples_info


def get_dhp_source(i: DpdHeadword):
    """Get DHP source info from SBS info in a DpdHeadword object."""

    dhp_sources = []
    dhp_suttas = []
    dhp_examples = []

    sources = [i.source_1, i.source_2]
    if i.sbs:
        sources.extend([i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4])

    for source in sources:
        if source and "DHP" in source and "a" not in source:
            dhp_sources.append(source)
            dhp_suttas.append(i.sutta_1 if source == i.source_1 else i.sutta_2 if source == i.source_2 else getattr(i.sbs, f'sbs_sutta_{sources.index(source) - 1}'))
            dhp_examples.append(i.example_1 if source == i.source_1 else i.example_2 if source == i.source_2 else getattr(i.sbs, f'sbs_example_{sources.index(source) - 1}'))

    # Choose the source with the smallest number
    if dhp_sources:
        dhp_source = min(dhp_sources, key=lambda x: int(re.findall(r'\d+', x)[0]))
        dhp_sutta = dhp_suttas[dhp_sources.index(dhp_source)]
        dhp_example = dhp_examples[dhp_sources.index(dhp_source)]

        dhp_example_info = [
            dhp_source,
            dhp_sutta,
            dhp_example,
        ]
    else:
        dhp_example_info = [
            "",
            "",
            "",
        ]

    return dhp_example_info


def get_paritta_source(i: DpdHeadword, chant_names: List[str]) -> List[str]:
    """Get Paritta source info from SBS info in a DpdHeadword object."""
    sbs_sources = [i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4]
    sbs_suttas = [i.sbs.sbs_sutta_1, i.sbs.sbs_sutta_2, i.sbs.sbs_sutta_3, i.sbs.sbs_sutta_4]
    sbs_examples = [i.sbs.sbs_example_1, i.sbs.sbs_example_2, i.sbs.sbs_example_3, i.sbs.sbs_example_4]
    sbs_palichants = [i.sbs.sbs_chant_pali_1, i.sbs.sbs_chant_pali_2, i.sbs.sbs_chant_pali_3, i.sbs.sbs_chant_pali_4]

    for source, sutta, example, palichant in zip(sbs_sources, sbs_suttas, sbs_examples, sbs_palichants):
        if any(chant_name in palichant for chant_name in chant_names):
            return [
                source,
                sutta,
                example,
            ]

    return [
        "",
        "",
        "",
    ]


def get_vibhanga_source(i: DpdHeadword, vibhanga_sources: List[str]) -> List[str]:
    """Get Vibhanga source info from SBS info in a DpdHeadword object."""
    sbs_sources = [i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4]
    sbs_suttas = [i.sbs.sbs_sutta_1, i.sbs.sbs_sutta_2, i.sbs.sbs_sutta_3, i.sbs.sbs_sutta_4]
    sbs_examples = [i.sbs.sbs_example_1, i.sbs.sbs_example_2, i.sbs.sbs_example_3, i.sbs.sbs_example_4]

    for source, sutta, example in zip(sbs_sources, sbs_suttas, sbs_examples):
        if any(vibhanga_source in source for vibhanga_source in vibhanga_sources):
            return [
                source,
                sutta,
                example,
            ]

    return [
        "",
        "",
        "",
    ]


def dhp(dpspth, dpd_db):
    """ Returns a list of rows for dhp csv. """
    console.print("[yellow]making dhp csv")

    def _is_needed(i: DpdHeadword) -> bool:
        sources = [i.source_1, i.source_2]
        if i.sbs:
            sources.extend([i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4])

        return bool(any(re.search(r'DHP\d', source) for source in sources))

    columns_names = ['id', 'pali', 'grammar', 'neg', 'verb', 'trans', 
        'plus_case', 'meaning', 'meaning_lit', 'native', 'sanskrit', 
        'sanskrit_root', 'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 
        'root_has_verb', 'root_group', 'root_sign', 'root_meaning', 'root_base', 
        'construction', 'derivative', 'suffix', 'phonetic', 'compound_type', 
        'compound_construction', 'source', 'sutta', 'example', 
        'link', 'audio', 'test', 'feedback', 'marks']

    def dhp_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
            i.lemma_1,
            *get_grammar_and_meaning(i),
            "",
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_dhp_source(i),
            i.link.replace("\n", "<br>") if i.link else None,
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "dhp"),
        ]

        return none_to_empty(fields)

    rows = (dhp_row(i) for i in dpd_db if _is_needed(i))
    rows_list = list(rows)
    # Sort rows based on source
    sorted_rows = sorted(rows_list, key=lambda x: int(re.findall(r'\d+', x[26])[0]))

    # Save anki_dhp to csv file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_dhp.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(sorted_rows)
    console.print(f"[bold] {len(sorted_rows)}[/bold] [green]rows has been saved to csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-dhp.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the DHP columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def sbs_per(dpspth, dpd_db):
    """ Returns a list of rows for sbs_per csv. """
    console.print("[yellow]making sbs per csv")

    def _is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_index)

    columns_names = ['id', 'pali', 'grammar', 'neg', 'verb', 'trans', 'plus_case',
        'meaning', 'meaning_lit', 'native', 'sbs_meaning', 'sanskrit', 
        'sanskrit_root', 'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 
        'root_has_verb', 'root_group', 'root_sign', 'root_meaning', 'root_base', 
        'construction', 'derivative', 'suffix', 'phonetic', 'compound_type', 
        'compound_construction', 'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 
        'sbs_chant_pali_1', 'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2',
        'sbs_sutta_2', 'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 
        'sbs_chapter_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 
        'sbs_chant_pali_3', 'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 
        'sbs_sutta_4', 'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 
        'sbs_chapter_4', 'antonym', 'synonym', 'variant', 'commentary', 'notes', 
        'sbs_notes', 'link', 'sbs_index', 'audio', 'test', 'feedback', 'marks']

    def sbs_row(i: DpdHeadword) -> List[str]:

        tags = join(
            i.sbs.sbs_chant_pali_1, 
            i.sbs.sbs_chant_pali_2, 
            i.sbs.sbs_chant_pali_3, 
            i.sbs.sbs_chant_pali_4
            )

        fields = [
            i.id,
            i.lemma_1,
            *get_grammar_and_meaning(i),
            "",
            i.sbs.sbs_meaning if i.sbs else None,
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_sbs_info(i),
            i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
            i.link.replace("\n", "<br>") if i.link else None,
            i.sbs.sbs_index if i.sbs else None,
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "sbs"),
            tags,
        ]

        return none_to_empty(fields)

    rows = (sbs_row(i) for i in dpd_db if _is_needed(i))
    rows_list = list(rows)

    # Save anki_sbs to csv file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_sbs.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_list)
    console.print(f"[bold] {len(rows_list)}[/bold] [green]rows has been saved to csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-sbs.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the SBS columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def parittas(dpspth, dpd_db):
    """ Returns a list of rows for parittas csv. """
    console.print("[yellow]making parittas csv")

    chant_names = ["Karaṇīya-metta-sutta", "Ratana-sutta", "Maṅgala-sutta"]

    def _is_needed(i: DpdHeadword):
        if i.sbs:
            sources = [i.sbs.sbs_chant_pali_1, i.sbs.sbs_chant_pali_2, i.sbs.sbs_chant_pali_3, i.sbs.sbs_chant_pali_4]
            return bool(any(chant_name in source for source in sources for chant_name in chant_names))

    columns_names = ['id', 'pali', 'grammar', 'meaning', 'meaning_lit', 'root', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'source', 'sutta', 'example', 'audio', 'test', 'feedback', 'marks']

    def parittas_row(i: DpdHeadword, chant_names) -> List[str]:
        
        if i.rt is not None:
            root_key = re.sub(r" \d*$", "", str(i.root_key))
        fields = [
            i.id,
            i.lemma_1,
            i.grammar,
            i.meaning_1 if i.meaning_1 else i.meaning_2,
            i.meaning_lit,
            root_key if i.rt else None,
            i.rt.root_group if i.rt else None,
            i.root_sign if i.rt else None,
            i.rt.root_meaning if i.rt else None,
            i.root_base if i.rt else None,
            i.construction.replace("\n", "<br>") if i.construction else None,
            *get_paritta_source(i, chant_names),
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "paritta"),
        ]

        return none_to_empty(fields)

    rows = (parittas_row(i, chant_names) for i in dpd_db if _is_needed(i))
    rows_list = list(rows)
    # Sort rows based on source
    sorted_rows = sorted(rows_list, key=lambda x: x[11])

    # Save anki_sbs to csv file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_parittas.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(sorted_rows)
    console.print(f"[bold] {len(sorted_rows)}[/bold] [green]rows has been saved to csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-parittas.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the Parittas columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def dps(dpspth, dpd_db):
    """ Returns a list of rows for dps csv. """
    console.print("[yellow]making dps csv")

    def _is_needed(i: DpdHeadword):
        if i.sbs:
            sources = [i.sbs.sbs_source_1, i.sbs.sbs_source_2, i.sbs.sbs_source_3, i.sbs.sbs_source_4]
            return bool(i.ru and any(source for source in sources if source))

    columns_names = ['id', 'pali', 'sbs_class_anki', 'sbs_category', 'sbs_class', 
    'sbs_patimokkha', 'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning', 
    'meaning_lit', 'ru_meaning', 'ru_meaning_lit', 'sbs_meaning', 'sanskrit', 'sanskrit_root', 
    'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
    'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
    'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
    'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 
    'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2', 'sbs_sutta_2', 
    'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2', 
    'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 
    'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 
    'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4', 
    'antonym', 'synonym', 'variant', 'commentary', 'notes', 'sbs_notes', 
    'ru_notes', 'link', 'sbs_index', 'audio', 'test', 'feedback', 'marks']

    def dps_row(i: DpdHeadword) -> List[str]:

        if i.rt is not None:
            root_key = re.sub(r" \d*$", "", str(i.root_key))

        fields = [
            i.id,
            i.lemma_1,
            i.sbs.sbs_class_anki if i.sbs else None, 
            i.sbs.sbs_category if i.sbs else None,
            i.sbs.sbs_class if i.sbs else None,
            i.sbs.sbs_patimokkha if i.sbs else None,
            *get_grammar_and_meaning(i),
            i.ru.ru_meaning if i.ru else None,
            i.ru.ru_meaning_lit if i.ru else None,
            i.sbs.sbs_meaning if i.sbs else None,
            i.sanskrit,
            i.rt.sanskrit_root if i.rt else None,
            i.rt.sanskrit_root_meaning if i.rt else None,
            i.rt.sanskrit_root_ru_meaning if i.rt else None,
            i.rt.sanskrit_root_class if i.rt else None,
            root_key if i.rt else None,
            i.rt.root_has_verb if i.rt else None,
            i.rt.root_group if i.rt else None,
            i.root_sign if i.rt else None,
            i.rt.root_meaning if i.rt else None,
            i.rt.root_ru_meaning if i.rt else None,
            i.root_base if i.rt else None,
            *get_construction(i),
            *get_sbs_info(i),
            i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
            i.ru.ru_notes.replace("\n", "<br>") if i.ru else None,
            i.link.replace("\n", "<br>") if i.link else None,
            i.sbs.sbs_index if i.sbs else None,
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "dps"),
        ]

        return none_to_empty(fields)

    rows = (dps_row(i) for i in dpd_db if _is_needed(i))
    rows_list = list(rows)

    # Save anki_sbs to csv file
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_dps.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_list)
    console.print(f"[bold] {len(rows_list)}[/bold] [green]rows has been saved to csv")
    
    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-dps.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the DPS columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def classes(dpspth, dpd_db, unique_sbs_class_values):
    """ Returns a list of rows for classes csvs. """
    console.print("[yellow]making classes csv")

    def _is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_class_anki)

    columns_names = ['id', 'pali', 'sbs_class_anki', 
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning', 'meaning_lit', 
        'native', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_chant_pali_1', 
        'sbs_chant_eng_1', 'sbs_chapter_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_chant_pali_2', 'sbs_chant_eng_2', 'sbs_chapter_2', 
        'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_chant_pali_3', 
        'sbs_chant_eng_3', 'sbs_chapter_3', 'sbs_source_4', 'sbs_sutta_4', 
        'sbs_example_4', 'sbs_chant_pali_4', 'sbs_chant_eng_4', 'sbs_chapter_4', 
        'antonym', 'synonym', 'variant', 'commentary', 'notes', 'sbs_notes', 'link', 
        'audio', 'test', 'feedback', 'marks']

    def classes_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
            i.lemma_1,
            i.sbs.sbs_class_anki if i.sbs else None, 
            *get_grammar_and_meaning(i),
            "",
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_sbs_info(i),
            i.sbs.sbs_notes.replace("\n", "<br>") if i.sbs else None,
            i.link.replace("\n", "<br>") if i.link else None,
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "class"),
        ]

        return none_to_empty(fields)

    # Save clases one by one to csvs
    for sbs_class_value in unique_sbs_class_values:
        output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', f"class_{sbs_class_value}.csv")
        with open(output_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows((classes_row(i) for i in dpd_db if _is_needed(i) and i.sbs.sbs_class_anki == sbs_class_value))

    # Save all basic classes to csv
    all_sbs_class_values = [value for value in unique_sbs_class_values if 1 <= value <= 29]
    all_classes = []
    for sbs_class_value in all_sbs_class_values:
        rows = (classes_row(i) for i in dpd_db if _is_needed(i) and i.sbs.sbs_class_anki == sbs_class_value)
        all_classes += rows
    all_classes_list = list(all_classes)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "class_all.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(all_classes_list)
    console.print(f"[bold] {len(all_classes_list)}[/bold] [green]rows has been saved to class_all.csv")

    # Save ru for all basic classes to csv
    def ru_classes_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
        ]

        if i.ru.ru_meaning_lit:
            ru_meaning = i.ru.ru_meaning + '; досл. ' + i.ru.ru_meaning_lit
        else:
            ru_meaning = i.ru.ru_meaning
        fields.append(ru_meaning)

        return none_to_empty(fields)

    ru_all_classes = []
    for sbs_class_value in all_sbs_class_values:
        rows = (ru_classes_row(i) for i in dpd_db if _is_needed(i) and i.sbs.sbs_class_anki == sbs_class_value and i.ru)
        ru_all_classes += rows
    ru_all_classes_list = list(ru_all_classes)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "class_ru.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(ru_all_classes_list)

    # Save all classes including upcoming
    rows_total = (classes_row(i) for i in dpd_db if _is_needed(i))
    rows_total_list = list(rows_total)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', "class_total.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_total_list)

    # Save class_upcoming to a CSV file
    all_classes_set = set((tuple(row) for row in all_classes_list))
    rows_upcoming = [row for row in rows_total_list if tuple(row) not in all_classes_set]
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'classes', "class_upcoming.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_upcoming)

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-vocab-class.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the Class columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def suttas(dpspth, dpd_db, unique_sbs_category_values):
    """ Returns a list of rows for suttas csv. """
    console.print("[yellow]making suttas csv")

    def _is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_category)

    columns_names = ['id', 'pali', 'sbs_category', 
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning', 'meaning_lit', 
        'native', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_source_4',
        'sbs_sutta_4', 'sbs_example_4', 'antonym', 'synonym', 'variant', 'commentary', 
        'notes', 'sbs_notes', 'link', 'audio', 'test', 'feedback', 'marks']

    def suttas_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
            i.lemma_1,
            i.sbs.sbs_category if i.sbs else None, 
            *get_grammar_and_meaning(i),
            "",
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_examples(i),
            current_date,
            get_feedback(i, "suttas"),
        ]

        return none_to_empty(fields)

    # Save category one by one to csvs
    for sbs_category_value in unique_sbs_category_values:
        output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', 'suttas', f"{sbs_category_value}.csv")
        with open(output_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows((suttas_row(i) for i in dpd_db if _is_needed(i) and i.sbs.sbs_category == sbs_category_value))

    # Save all sbs_category
    rows_total = (suttas_row(i) for i in dpd_db if _is_needed(i))
    rows_total_list = list(rows_total)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "suttas_class.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_total_list)
    console.print(f"[bold] {len(rows_total_list)}[/bold] [green]rows has been saved to csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-suttas-class.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the Suttas columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def root_phonetic_class(dpspth, dpd_db, unique_sbs_class_values):
    """ Returns a list of rows for root and phonetic csvs. """
    console.print("[yellow]making root and phonetic  csvs")

    def root_is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_class_anki and i.rt)

    def phonetic_is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_class_anki and i.phonetic)

    columns_names = ['id', 'pali', 'sbs_class_anki',
        'grammar', 'neg', 'verb', 'trans', 'plus_case', 'meaning', 'meaning_lit', 
        'native', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'sbs_source_1', 'sbs_sutta_1', 'sbs_example_1', 'sbs_source_2', 'sbs_sutta_2', 
        'sbs_example_2', 'sbs_source_3', 'sbs_sutta_3', 'sbs_example_3', 'sbs_source_4',
        'sbs_sutta_4', 'sbs_example_4', 'antonym', 'synonym', 'variant', 'commentary', 
        'notes', 'sbs_notes', 'link', 'audio', 'test', 'feedback', 'marks']

    def root_phonetic_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
            i.lemma_1,
            i.sbs.sbs_class_anki if i.sbs else None, 
            *get_grammar_and_meaning(i),
            "",
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_examples(i),
            current_date,
            get_feedback(i, "root-phonetic"),
        ]

        return none_to_empty(fields)

    all_sbs_class_values = [value for value in unique_sbs_class_values if 1 <= value <= 29]

    # Save all root for basic classes to csv
    rows_total = []
    for sbs_class_value in all_sbs_class_values:
        rows = (root_phonetic_row(i) for i in dpd_db if root_is_needed(i) and i.sbs.sbs_class_anki == sbs_class_value)
        rows_total += rows
    rows_total_list = list(rows_total)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "roots_class.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_total_list)
    console.print(f"[bold] {len(rows_total_list)}[/bold] [green]rows has been saved to roots_class.csv")

    # Save all phonetic for basic classes to csv
    rows_total = []
    for sbs_class_value in all_sbs_class_values:
        rows = (root_phonetic_row(i) for i in dpd_db if phonetic_is_needed(i) and i.sbs.sbs_class_anki == sbs_class_value)
        rows_total += rows
    rows_total_list = list(rows_total)
    # sorted_rows = sorted(rows_total_list, key=lambda x: x[2]) # Sort rows based on class number
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', "phonetic_class.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(rows_total_list)
    console.print(f"[bold] {len(rows_total_list)}[/bold] [green]rows has been saved to phonetic_class.csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        with open(f'{dpspth.sbs_anki_style_dir}/field-list-roots-class.txt', 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] names of the Root columns [/green]([bold]{len(columns_names)}[/bold]) [green]are saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")


def vibhanga(dpspth, dpd_db):
    """ Returns a list of rows for vibhanga csv. """
    console.print("[yellow]making vibhanga csv")

    sources_names = ["VIN1", "VIN2"]

    def _is_needed(i: DpdHeadword):
        return bool(i.sbs and i.sbs.sbs_patimokkha == "vib")

    columns_names = ['id', 'pali', 'grammar', 'neg', 'verb', 'trans', 'plus_case',
        'meaning', 'meaning_lit', 'native', 'sanskrit', 'sanskrit_root', 
        'sanskrit_root_meaning', 'sanskrit_root_class', 'root', 'root_has_verb', 
        'root_group', 'root_sign', 'root_meaning', 'root_base', 'construction', 
        'derivative', 'suffix', 'phonetic', 'compound_type', 'compound_construction', 
        'source', 'sutta', 'example', 'antonym', 'synonym', 'variant', 'commentary', 
        'notes', 'link', 'audio', 'test', 'feedback', 'marks']

    def vibhanga_row(i: DpdHeadword) -> List[str]:
        fields = [
            i.id,
            i.lemma_1,
            *get_grammar_and_meaning(i),
            "",
            i.sanskrit,
            *get_root_info(i),
            *get_construction(i),
            *get_vibhanga_source(i, sources_names),
            i.antonym,
            i.synonym,
            i.variant,
            i.commentary.replace("\n", "<br>") if i.commentary else None,
            i.notes.replace("\n", "<br>") if i.notes else None,
            i.link.replace("\n", "<br>") if i.link else None,
            SBS_table_tools().generate_sbs_audio(i.lemma_clean),
            current_date,
            get_feedback(i, "vibhanga"),
        ]
        return none_to_empty(fields)

    rows_total = [vibhanga_row(i) for i in dpd_db if _is_needed(i)]
    
    # Verify the column index for "source" and "example"
    source_column_index = columns_names.index('source')
    example_column_index = columns_names.index('example')

    # Sort rows based on the hierarchical VIN value in the source column
    def parse_vin(value):
        # Extract the numerical parts from "VIN1.1.1" and return as a tuple of integers
        return tuple(map(int, re.findall(r'\d+', value)))

    def clean_html_tags(text):
        if text:
            return re.sub(r'<\/?b>', '', text)
        return text
    
    sorted_rows_total_list = sorted(
        rows_total,
        key=lambda x: (
            parse_vin(x[source_column_index]), 
            clean_html_tags(x[example_column_index])
            )
    )

    # Write sorted rows to CSV
    file_path = os.path.join(dpspth.anki_csvs_dps_dir, "anki_vibhanga.csv")
    with open(file_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(sorted_rows_total_list)
    console.print(f"[bold] {len(sorted_rows_total_list)}[/bold] [green]rows have been saved to csv")

    # Save the list of field names to a text file
    if dpspth.sbs_anki_style_dir:
        field_file_path = os.path.join(dpspth.sbs_anki_style_dir, 'field-list-vibhanga.txt')
        with open(field_file_path, 'w') as file:
            file.write('\n'.join(columns_names))
        console.print(f"[green] Column names ([bold]{len(columns_names)}[/bold]) saved to the txt")
    else:
        console.print("[bold red] sbs_anki_style_dir not found")



def native(dpspth, dpd_db):
    """ Returns a list of rows for sbs_rus csv. """
    console.print("[yellow]making native csvs")

    def _is_needed(i: DpdHeadword):
        return bool(i.sbs and (
            i.sbs.sbs_class_anki or
            i.sbs.sbs_category or
            i.sbs.sbs_patimokkha or
            i.sbs.sbs_index
        ))

    # Save ru for all sbs decks
    def ru_row(i: DpdHeadword) -> List[str]:

        if i.ru.ru_meaning_lit:
            ru_meaning = i.ru.ru_meaning + '; досл. ' + i.ru.ru_meaning_lit
        else:
            ru_meaning = i.ru.ru_meaning
        
        fields = [
            i.id,
            ru_meaning,
        ]

        return none_to_empty(fields)

    ru_all_sbs = []
    rows = (ru_row(i) for i in dpd_db if _is_needed(i) and i.ru)
    ru_all_sbs += rows
    ru_all_sbs_list = list(ru_all_sbs)
    output_path = os.path.join(dpspth.anki_csvs_dps_dir, "sbs_rus.csv")
    with open(output_path, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(ru_all_sbs_list)
    console.print(f"[bold] {len(ru_all_sbs_list)}[/bold] [green]rows has been saved to sbs_rus.csv")


def main():
    """ Makes anki csvs. """
    tic()
    console.print("[bold bright_yellow]exporting csvs for anki")

    pth = ProjectPaths()
    dpspth = DPSPaths()

    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()

    # make list of sbs classes
    unique_sbs_class_values = db_session.query(SBS.sbs_class_anki).filter(SBS.sbs_class_anki != "").distinct().all()
    unique_sbs_class_values = [value[0] for value in unique_sbs_class_values]
    unique_sbs_class_values.sort()

    # make list of sbs categories
    unique_sbs_category_values = db_session.query(SBS.sbs_category).filter(SBS.sbs_category != "").distinct().all()
    unique_sbs_category_values = [value[0] for value in unique_sbs_category_values]
    unique_sbs_category_values.sort()

    dpd_db = sorted(
        dpd_db, key=lambda x: pali_sort_key(x.lemma_1))
    console.print("[green] db has been set up and sorted successfully")

    dhp(dpspth, dpd_db)
    sbs_per(dpspth, dpd_db)
    parittas(dpspth, dpd_db)
    dps(dpspth, dpd_db)
    classes(dpspth, dpd_db, unique_sbs_class_values)
    suttas(dpspth, dpd_db, unique_sbs_category_values)
    root_phonetic_class(dpspth, dpd_db, unique_sbs_class_values)
    vibhanga(dpspth, dpd_db)
    native(dpspth, dpd_db)
    toc()


if __name__ == "__main__":
    main()