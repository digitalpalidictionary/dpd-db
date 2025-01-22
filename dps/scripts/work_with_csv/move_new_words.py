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

move_new_words_from_dps_backup()
