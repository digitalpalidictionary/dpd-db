#!/usr/bin/env python3

""" Filter words based on some codition and save into csv"""

from db.models import PaliWord
from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH
from db.get_db_session import get_db_session
import csv
from rich import print
from tools.tic_toc import tic, toc

def save_filtered_words():
    tic()
    print("[bright_yellow]filtering words from db by some condition")

    db_session = get_db_session(PTH.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()

    # Filter words based on sbs.sbs_class, also check if sbs is not None
    filtered_words = [word for word in dpd_db if word.sbs and word.sbs.sbs_class == '(ru)']

    # Sort the filtered words by sbs_class
    filtered_words = sorted(filtered_words, key=lambda word: word.sbs.sbs_class_anki)

    # Write to CSV using tab as delimiter
    with open(DPSPTH.temp_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['id', 'ru_meaning', 'meaning_1', 'sbs_class', 'sbs_class_anki']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()  # Write the header

        for word in filtered_words:
            writer.writerow({
                'id': word.id,
                'ru_meaning': word.ru.ru_meaning,
                'meaning_1': word.meaning_1,
                'sbs_class': word.sbs.sbs_class,
                'sbs_class_anki': word.sbs.sbs_class_anki
            })

    db_session.close()

    print(f"[green]saved into {DPSPTH.temp_csv_path}")

    toc()


# Call the function
save_filtered_words()
