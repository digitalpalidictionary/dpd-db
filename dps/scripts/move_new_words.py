#!/usr/bin/env python3

# move rows which ahve a bigger id from dps/backup/dpd_headwords.tsv into db/backup_tsv/dpd_headwords.tsv

import csv
import os
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths


def move_new_words():

    pth = ProjectPaths()
    dpspth = DPSPaths()

    dps_headwords_path = os.path.join(dpspth.dps_backup_dir, "dpd_headwords.tsv")
    pth.pali_word_path

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
        for row in reader:
            if int(row[0]) > max_id:
                writer.writerow(row)


move_new_words()