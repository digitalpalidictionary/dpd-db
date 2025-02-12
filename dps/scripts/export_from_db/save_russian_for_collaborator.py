#!/usr/bin/env python3

""" Filter all russian words with roots and comp and save into csv"""

from db.models import DpdHeadword, FamilyCompound
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv

from rich.console import Console

from tools.tic_toc import tic, toc
from tools.meaning_construction import make_meaning_combo

from typing import Optional, Dict, Union

from sqlalchemy.orm import joinedload
from sqlalchemy.orm import object_session

from concurrent.futures import ThreadPoolExecutor


console = Console()

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)


def process_word_root(word):
    return {
        'id': word.id,
        'lemma': word.lemma_1,
        'pos': word.pos,
        'root_key': word.root_key,
        'family_root': word.family_root,
        'meaning': make_meaning_combo(word),
        'ru_meaning': word.ru.ru_meaning,
        'ru_meaning_lit': word.ru.ru_meaning_lit,
        'ru_meaning_raw': word.ru.ru_meaning_raw if not word.ru.ru_meaning else "",
        'ru_cognate': word.ru.ru_cognate,
        'corrections_ru_meaning': "",
        'corrections_ru_meaning_lit': "",
        'notes': ""
    }


def save_total_ru_roots():
    tic()
    console.print("[bold bright_yellow]filtering words with roots")

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.rt), joinedload(DpdHeadword.ru)).filter(
        DpdHeadword.ru != None,
        DpdHeadword.meaning_1 != "",
        DpdHeadword.root_key != ""
    ).all()

    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

    filtered_words = sorted(
        dpd_db,
        key=lambda word: (word.rt.root_count if word.rt else 0, word.root_key, word.family_root),
        reverse=True
    )

    with open(dpspth.ru_total_root_path, 'w', newline='') as csvfile:
        fieldnames = [
            'id', 'lemma', 'pos', 'root_key', 'family_root', 'meaning',
            'ru_meaning', 'ru_meaning_lit', 'ru_meaning_raw', 'ru_cognate', 
            'corrections_ru_meaning', 'corrections_ru_meaning_lit', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor() as executor:
            results = executor.map(process_word_root, filtered_words)
            for result in results:
                writer.writerow(result)

    db_session.close()
    print(f"[green]saved into {dpspth.ru_total_root_path}")
    toc()


def get_family_compounds(i: DpdHeadword) -> Optional[Dict[str, Union[str, int]]]:
    db_session = object_session(i)
    if db_session is None:
        raise Exception("No db_session")

    if i.family_compound:
        fc = db_session \
            .query(FamilyCompound) \
            .filter(FamilyCompound.compound_family.in_(i.family_compound_list)) \
            .all()

        # Sort by order of the family compound list
        word_order = i.family_compound_list
        fc = sorted(fc, key=lambda x: word_order.index(x.compound_family))

    else:
        fc = db_session.query(FamilyCompound) \
            .filter(FamilyCompound.compound_family == i.lemma_clean) \
            .all()

    # Get the FamilyCompound with the highest count
    fc_max = max(fc, key=lambda x: x.count, default=None)

    if fc_max:
        return {'name': fc_max.compound_family, 'count': fc_max.count}
    else:
        return None


def process_word_comp(word):
    family_compound = get_family_compounds(word)
    return {
        'id': word.id,
        'lemma': word.lemma_1,
        'pos': word.pos,
        'family_compound_word': family_compound['name'] if family_compound else "",
        'count': family_compound['count'] if family_compound else 0,
        'meaning': make_meaning_combo(word),
        'ru_meaning': word.ru.ru_meaning,
        'ru_meaning_lit': word.ru.ru_meaning_lit,
        'ru_meaning_raw': word.ru.ru_meaning_raw if not word.ru.ru_meaning else "",
        'ru_cognate': word.ru.ru_cognate,
        'corrections_ru_meaning': "",
        'corrections_ru_meaning_lit': "",
        'notes': ""
    }


def save_total_ru_comps():
    tic()
    console.print("[bold bright_yellow]filtering comp words")

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).filter(
        DpdHeadword.ru != None,
        DpdHeadword.meaning_1 != "",
        DpdHeadword.family_compound != "",
        DpdHeadword.root_key == ""
    ).all()

    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

    filtered_words = dpd_db

    with open(dpspth.ru_total_comp_path, 'w', newline='') as csvfile:
        fieldnames = [
            'id', 'lemma', 'pos', 'family_compound_word', 'count',
            'meaning', 'ru_meaning', 'ru_meaning_lit', 'ru_meaning_raw', 'ru_cognate',
            'corrections_ru_meaning', 'corrections_ru_meaning_lit', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor() as executor:
            results = executor.map(process_word_comp, filtered_words)
            # Sort results by family_compound_count (descending) and family_compound_word (alphabetical)
            sorted_results = sorted(
                results,
                key=lambda x: (-x['count'], x['family_compound_word'])
            )
            for result in sorted_results:
                writer.writerow(result)

    db_session.close()
    print(f"[green]saved into {dpspth.ru_total_comp_path}")
    toc()


# Call the function
save_total_ru_roots()
save_total_ru_comps()
# TODO save_total_ru_word_families()
# TODO save_total_ru_sets()
# TODO save_total_ru_rest()