#!/usr/bin/env python3

""" Filter all russian words and save into csv"""

from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv

from rich.console import Console

from tools.tic_toc import tic, toc
from tools.meaning_construction import make_meaning_combo


from sqlalchemy.orm import joinedload

from concurrent.futures import ThreadPoolExecutor


console = Console()

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)


def process_word(word):
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
            'ru_meaning', 'ru_meaning_lit', 'ru_meaning_raw', 'corrections_ru_meaning',	
            'corrections_ru_meaning_lit', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor() as executor:
            results = executor.map(process_word, filtered_words)
            for result in results:
                writer.writerow(result)

    db_session.close()
    print(f"[green]saved into {dpspth.ru_total_root_path}")
    toc()


def save_total_ru_comp():
    tic()
    console.print("[bold bright_yellow]filtering words with comp")

    # Query to filter words based on the presence in the Russian table
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.ru)).filter(
        DpdHeadword.ru != None,
        DpdHeadword.meaning_1 != "",
        DpdHeadword.root_key == "",
        DpdHeadword.family_compound != ""
        ).all()
    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

        # Filter words and sort them in reverse order
    filtered_words = sorted(
        dpd_db,
        key=lambda word: (word.family_compound, word.family_compound, word.ebt_count),
        reverse=True
    )

    # Write to CSV using tab as delimiter
    with open(dpspth.ru_total_root_path, 'w', newline='') as csvfile:
        fieldnames = [
            'id', 'pos', 'lemma', 'family_comp_word', 'meaning',
            'ru_meaning', 'ru_meaning_lit', 'ru_meaning_raw', 'corrections_ru_meaning',	
            'corrections_ru_meaning_lit', 'notes'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()  # Write the header

        for word in filtered_words:
            writer.writerow({
                'id': word.id,
                'pos': word.pos,
                'lemma': word.lemma_1,
                'family_comp_word': word.family_compound,
                'meaning': make_meaning_combo(word),
                'ru_meaning': word.ru.ru_meaning,
                'ru_meaning_lit': word.ru.ru_meaning_lit,
                'ru_meaning_raw': word.ru.ru_meaning_raw if not word.ru.ru_meaning else "",
                'corrections_ru_meaning': "",
                'corrections_ru_meaning_lit': "",
                'notes': ""
            })

    db_session.close()

    print(f"[green]saved into {dpspth.ru_total_root_path}")

    toc()


# Call the function
save_total_ru_roots()
# save_total_ru_comp()