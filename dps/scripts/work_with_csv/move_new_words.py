#!/usr/bin/env python3

# add new words from the DPS backup or directly from additions.

import csv
import os
import pandas as pd
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

pth = ProjectPaths()
dpspth = DPSPaths()


# move words from dps backup
def move_new_words_from_dps_backup():

    print("adding additions from dps backup to db/backup/dpd_headwords.tsv")

    dps_headwords_path = os.path.join(dpspth.dps_backup_dir, "dpd_headwords.tsv")

    # Read the last ID from pali_word_new
    with open(pth.pali_word_path, 'r') as new_file:
        reader = csv.reader(new_file, delimiter='\t')
        next(reader)  # Skip the header row
        max_id = max(int(row[0]) for row in reader)

    # Append rows from pali_word_old with IDs greater than max_id to pali_word_new
    with open(dps_headwords_path, 'r') as dps_file, open(pth.pali_word_path, 'a', newline='') as new_file:
        reader = csv.reader(dps_file, delimiter='\t')
        writer = csv.writer(new_file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
        next(reader)  # Skip the header row
        added_rows_count = 0
        for row in reader:
            if int(row[0]) > max_id:
                writer.writerow(row)
                added_rows_count += 1
                print(f" {added_rows_count}: {row[0]}, {row[1]}, {row[4]}, {row[10]}")

    print(f"Total rows added: {added_rows_count}")


# add words from additions
#! not really working
def add_new_words_from_additions():

    print("adding additions to db/backup/dpd_headwords.tsv")

    # Load the TSV files
    dpd_headwords_df = pd.read_csv(pth.pali_word_path, sep='\t', low_memory=False)
    additions_df = pd.read_csv(pth.additions_tsv_path, sep='\t', low_memory=False)

    # Exclude columns (if needed based on how you loaded the original file)
    exclude_columns = [
        "created_at", "updated_at", "inflections", "inflections_sinhala", 
        "inflections_devanagari", "inflections_thai", "inflections_html",
        "freq_html", "ebt_count"
    ]

    # Remove excluded columns from additions_df (if they exist)
    additions_df = additions_df[[col for col in additions_df.columns if col not in exclude_columns]]

    # Find common columns
    common_columns = list(set(dpd_headwords_df.columns).intersection(set(additions_df.columns)))

    # Filter rows from additions_df where 'lemma_1' is not in dpd_headwords_df
    new_rows = additions_df[~additions_df['lemma_1'].isin(dpd_headwords_df['lemma_1'])]

    # Make sure there are no mismatches in column names by selecting common columns
    new_rows = new_rows[common_columns]

    # Check for any NaN values in the new rows, especially for critical columns like 'id'
    if new_rows['id'].isna().any():
        print("Warning: Some rows in the 'id' column are NaN. Please check the source data.")

    # Append the new rows to the existing TSV file
    with open(pth.pali_word_path, 'a', newline='') as tsvfile:  # Open in 'a' mode for appending
        # Create the CSV writer object with the desired configuration
        csvwriter = csv.writer(tsvfile, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
        
        # Write each new row of data to the existing file
        for index, row in new_rows.iterrows():
            csvwriter.writerow(row)

    print(f'New rows added to {pth.pali_word_path}')


move_new_words_from_dps_backup()

# add_new_words_from_additions()