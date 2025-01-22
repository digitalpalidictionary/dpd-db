#!/usr/bin/env python3

""" 
Filter all words with into csv and sort them by root frequence
also filter all roots 
"""

from db.models import DpdHeadword, DpdRoot
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


def process_word_root(word):
    return {
        'lemma': word.lemma_1,
        'sanskrit': word.sanskrit,
        'pos': word.pos,
        'root_key': word.root_key,
        'sk root': word.rt.sanskrit_root if word.root_key else "",
        'family_root': word.family_root,
        'meaning': make_meaning_combo(word),
    }


def save_words():
    tic()
    console.print("[bold bright_yellow]filtering all words")

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.rt)).all()

    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

    filtered_words = sorted(
        dpd_db,
        key=lambda word: (word.rt.root_count if word.rt else 0, word.root_key, word.family_root),
        reverse=True
    )

    with open(dpspth.total_words_path, 'w', newline='') as csvfile:
        fieldnames = [
            'lemma', 'sanskrit', 'pos', 'root_key', 'sk root', 'family_root', 'meaning'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor() as executor:
            results = executor.map(process_word_root, filtered_words)
            for result in results:
                writer.writerow(result)

    db_session.close()
    print(f"[green]saved into {dpspth.total_words_path}")
    toc()


def process_root(rt):
    return {
        'root': rt.root,
        'sanskrit': rt.sanskrit_root,
        'count': rt.root_count,
    }


def save_roots():
    tic()
    console.print("[bold bright_yellow]filtering roots")

    dpd_db = db_session.query(DpdRoot).all()

    print(f"Total rows that fit the filter criteria: {len(dpd_db)}")

    filtered_words = sorted(
        dpd_db,
        key=lambda rt: (rt.root_count),
        reverse=True
    )

    with open(dpspth.total_roots_path, 'w', newline='') as csvfile:
        fieldnames = [
            'root', 'sanskrit', 'count'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()

        with ThreadPoolExecutor() as executor:
            results = executor.map(process_root, filtered_words)
            for result in results:
                writer.writerow(result)

    db_session.close()
    print(f"[green]saved into {dpspth.total_roots_path}")
    toc()



# Call the function
save_words()
save_roots()
