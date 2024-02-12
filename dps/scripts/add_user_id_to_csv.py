#!/usr/bin/env python3

"""
Adding column user_id to desired csv using old file with user_id linked with id
"""

import os

import pandas as pd

from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

pth = ProjectPaths()
dpspth = DPSPaths()

deck = "anki_dhp"
csv_to_update = deck + ".csv"

# file_to_update_path = os.path.join(dpspth.anki_csvs_dps_dir, 'pali_class', csv_to_update)
file_to_update_path = os.path.join(dpspth.anki_csvs_dps_dir, csv_to_update)
file_to_update = pd.read_csv(file_to_update_path, sep='\t')

file_with_user_id_path = os.path.join(dpspth.temp_csv_backup_dir, "paliword_user_id.tsv")
file_with_user_id = pd.read_csv(file_with_user_id_path, sep='\t')

file_with_user_id = file_with_user_id[['id', 'user_id']]

# Merge the DataFrames on 'id' columns
merged = pd.merge(file_with_user_id, file_to_update, on=['id'], how='inner')

# Reorder columns
merged = merged[['user_id', 'id'] + [col for col in merged.columns if col not in ['user_id', 'id']]]

# Save to a TSV file
output_file_name = deck + "_user_id.csv"
output_path = os.path.join(pth.temp_dir, output_file_name)

# Save the filtered rows to a TSV file
merged.to_csv(output_path, sep='\t', index=False)
print(f"{deck} with user_id saved to {output_path}")






