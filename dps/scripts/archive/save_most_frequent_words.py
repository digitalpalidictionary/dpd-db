#!/usr/bin/env python3

""" Filter most frequent words into csv with limiting the number. Also not incluading those which already has been filtered."""

from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
import csv
import os

from rich.console import Console

from tools.tic_toc import tic, toc

from tools.date_and_time import year_month_day

date = year_month_day()

console = Console()


def save_filtered_words():
    tic()
    console.print("[bold bright_yellow]filtering most frequent words from db")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).filter(
        DpdHeadword.meaning_1 != "",
        DpdHeadword.ebt_count != "0",
    ).order_by(DpdHeadword.ebt_count.desc()).all()

    # Read existing IDs from CSV files in the directory
    existing_ids = set()
    for file in os.listdir(dpspth.freqent_words_dir):
        if file.endswith('.csv'):
            with open(os.path.join(dpspth.freqent_words_dir, file), 'r') as csvfile:
                reader = csv.DictReader(csvfile, delimiter='\t')
                for row in reader:
                    existing_ids.add(row['id'])

    # Filter out existing IDs and limit to 300
    filtered_dpd_db = [word for word in dpd_db if str(word.id) not in existing_ids][:300]

    file_name = f'{date}.csv'
    full_file_path = os.path.join(dpspth.freqent_words_dir, file_name)

    # Write to CSV using tab as delimiter first 300
    with open(full_file_path, 'w', newline='') as csvfile:
        fieldnames = ['id', 'pali', 'pos', 'meaning']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')

        writer.writeheader()  # Write the header

        for word in filtered_dpd_db:
            writer.writerow({
                'id': word.id,
                'pali': word.lemma_1,
                'pos': word.pos,
                'meaning': word.meaning_1,
            })

    db_session.close()

    print(f"[green]saved into {full_file_path}")

    toc()


# Call the function
save_filtered_words()
