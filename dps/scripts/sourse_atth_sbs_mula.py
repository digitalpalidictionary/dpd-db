#!/usr/bin/env python3

""" Filter words which has only commentary example in DPD but sutta example in SBS"""

from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv
import os
import shutil
from rich.console import Console

from tools.tic_toc import tic, toc
from datetime import datetime

from sqlalchemy.orm import joinedload

console = Console()


def save_filtered_words():
    tic()
    console.print("[bold bright_yellow]filtering words from db by some condition")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs), joinedload(DpdHeadword.ru)).all()

    commentary_list = [
            "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
            "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
            "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
            "NIDD1", "NIDD2", "PMa", "NPa", "NPt", "PTP",
            "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
            "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
            "VISM", "VISMa",
            "PRS", "SDM", "SPM",
            "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
            "buddhavandana", "Thai", "Sri Lanka", "Trad", "PAT PK", "MJG"
            ]

    filtered_words = [
        word for word in dpd_db
        if (
            any(comment in word.source_1 for comment in commentary_list) and
            not word.source_2 and
            any(
                getattr(word.sbs, f'sbs_source_{i}', None) and
                not any(comment in getattr(word.sbs, f'sbs_source_{i}', '') for comment in commentary_list)
                for i in range(1,  5)
            )
        )
    ]

    filtered_words_2 = [
        word for word in dpd_db
        if (
            any(comment in word.source_1 for comment in commentary_list) and
            any(comment in word.source_2 for comment in commentary_list) and
            any(
                getattr(word.sbs, f'sbs_source_{i}', None) and
                not any(comment in getattr(word.sbs, f'sbs_source_{i}', '') for comment in commentary_list)
                for i in range(1,  5)
            )
        )
    ]

    filtered_words_3 = [
        word for word in dpd_db
        if (
            any(
                getattr(word, f'source_{i}', None) and
                any(comment in getattr(word, f'source_{i}', '') for comment in commentary_list)
                for i in range(1,  3)
            ) and
            any(
                getattr(word.sbs, f'sbs_source_{i}', None) and
                not any(comment in getattr(word.sbs, f'sbs_source_{i}', '') for comment in commentary_list)
                for i in range(1,  5)
            )
        )
    ]


    # Sort the filtered words by sbs_class
    # filtered_words = sorted(filtered_words, key=lambda word: str(word.sbs.sbs_class_anki))

    # Check if the CSV exists, and create a backup with a timestamp if it does
    if os.path.exists(dpspth.temp_csv_path):
        timestamp = datetime.now().strftime('%y%m%d%H%M')
        base_name = os.path.basename(dpspth.temp_csv_path).replace('.csv', '')
        
        # Ensure the backup directory exists, if not, create it
        if not os.path.exists(dpspth.temp_csv_backup_dir):
            os.makedirs(dpspth.temp_csv_backup_dir)

        print(f"[green]backup existing csv into {dpspth.temp_csv_backup_dir}")

        backup_name = os.path.join(dpspth.temp_csv_backup_dir, f"{base_name}_backup_{timestamp}.csv")
        shutil.copy(dpspth.temp_csv_path, backup_name)

    # Write to CSV using tab as delimiter
    with open(dpspth.temp_csv_path, 'w', newline='') as csvfile:
        fieldnames = ['id', 'meaning_1']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()  # Write the header

        for word in filtered_words_3:
            writer.writerow({
                'id': word.id,
                'meaning_1': word.meaning_1,
            })
        
    # Read the existing CSV and count the number of rows
    with open(dpspth.temp_csv_path, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        row_count = sum(1 for row in reader) -  1  # Subtract  1 to exclude the header

    print(f"[green]Total rows in existing CSV: {row_count}")


    db_session.close()

    print(f"[green]saved into {dpspth.temp_csv_path}")

    toc()


# Call the function
save_filtered_words()
