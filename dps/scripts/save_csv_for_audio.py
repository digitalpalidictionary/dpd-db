#!/usr/bin/env python3

"""
    saving all words which dose not have an audio file. Saving them separately and unite them into one csv
"""

import csv
import os
import re
from db.models import DpdHeadword, SBS
from db.db_helpers import get_db_session
from tools.paths import ProjectPaths
from rich.console import Console
from dps.tools.paths_dps import DPSPaths

from sqlalchemy import between

from dps.tools.sbs_table_functions import SBS_table_tools

pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)

console = Console()

def main():
    console.print("Saving words based on specified criteria")

    # First CSV: sbs_class_anki from 1 to 29
    save_words_to_csv(between(SBS.sbs_class_anki, 1, 30), 'sbs_class.csv')

    # Second CSV: Non-empty sbs_index
    save_words_to_csv(SBS.sbs_index != '', 'per.csv')


    # Third CSV: Non-empty sbs_category
    save_words_to_csv(SBS.sbs_category != '', 'advanced_suttas.csv')

    db_session.close()

    # Call the function to extract first row from patimokkha
    clean_and_save_csv(os.path.join(dpspth.anki_csvs_dps_dir, 'anki_patimokkha.csv'), os.path.join(dpspth.csvs_for_audio_dir, 'patimokkha.csv'))

    # Call the function to unite the CSVs
    unite_csvs()

def save_words_to_csv(conditions, filename):

    words = db_session.query(DpdHeadword).join(SBS).filter(conditions).all()

    with open(os.path.join(dpspth.csvs_for_audio_dir, filename), 'w', newline='') as csvfile:
        fieldnames = ['pali']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        seen_palis = set() # Set to keep track of unique lemma_clean values

        for word in words:
            if word.sbs and not SBS_table_tools().generate_sbs_audio(word.lemma_clean):
                if word.lemma_clean not in seen_palis:
                    writer.writerow({
                        'pali': word.lemma_clean,
                    })
                    seen_palis.add(word.lemma_clean) # Add the lemma_clean value to the set


def unite_csvs():
    # Define the paths to the CSV files
    csv_files = [
        os.path.join(dpspth.csvs_for_audio_dir, 'sbs_class.csv'),
        os.path.join(dpspth.csvs_for_audio_dir, 'per.csv'),
        os.path.join(dpspth.csvs_for_audio_dir, 'advanced_suttas.csv'),
        os.path.join(dpspth.csvs_for_audio_dir, 'patimokkha.csv'),
    ]

    # Read each CSV file into a list of dictionaries
    all_data = []
    for csv_file in csv_files:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                # Extract the first column and clean it
                pali = clean_pali(row[0].strip())
                all_data.append({'pali': pali})

    # Remove duplicates based on the 'pali' key
    seen_palis = set()
    unique_data = []
    for row in all_data:
        if row['pali'] not in seen_palis:
            unique_data.append(row)
            seen_palis.add(row['pali'])

    # Write the combined, deduplicated data to a new CSV file
    with open(os.path.join(dpspth.csvs_for_audio_dir, 'united.csv'), 'w', newline='') as f:
        fieldnames = ['pali']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_data)


def clean_and_save_csv(input_filename, output_filename):
    # Open the input CSV file
    with open(input_filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader) # Skip the header

        # Extract the first column, clean it, and remove duplicates
        seen_values = set()
        cleaned_data = []
        for row in reader:
            pali = clean_pali(row[0])
            if not SBS_table_tools().generate_sbs_audio(pali) and pali not in seen_values:
                cleaned_data.append([pali])
                seen_values.add(pali)

    # Write the cleaned data to the output CSV file
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter='\t')
        writer.writerows(cleaned_data)

def clean_pali(pali):
    return re.sub(r'\d|\s|-', '', pali)



if __name__ == "__main__":
    main()