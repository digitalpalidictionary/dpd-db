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

console = Console()


def save_total_ru():
    tic()
    console.print("[bold bright_yellow]filtering words from db by some condition")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # Query to filter words based on the presence in the Russian table
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.rt), joinedload(DpdHeadword.ru)).filter(
        DpdHeadword.ru != None,
        DpdHeadword.meaning_1 != ""
        ).all()
    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

        # Filter words and sort them in reverse order
    filtered_words = sorted(
        dpd_db,
        key=lambda word: (word.rt.root_count if word.rt else 0, word.root_key, word.family_root),
        reverse=True
    )

    # Write to CSV using tab as delimiter
    with open(dpspth.ru_total_path, 'w', newline='') as csvfile:
        fieldnames = [
            'id', 'lemma', 'root_key', 'family_root', 'meaning',
            'ru_meaning', 'ru_meaning_lit', 'ru_meaning_raw'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()  # Write the header

        for word in filtered_words:
            writer.writerow({
                'id': word.id,
                'lemma': word.lemma_1,
                'root_key': word.root_key,
                'family_root': word.family_root,
                'meaning': make_meaning_combo(word),
                'ru_meaning': word.ru.ru_meaning,
                'ru_meaning_lit': word.ru.ru_meaning_lit,
                'ru_meaning_raw': word.ru.ru_meaning_raw if not word.ru.ru_meaning else "",
            })

    db_session.close()

    print(f"[green]saved into {dpspth.ru_total_path}")

    toc()


# Call the function
save_total_ru()