#!/usr/bin/env python3

"""find changed pali_1 from last check date, and save it into csv for compare what has been changed"""

import os

import pandas as pd

from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

pth = ProjectPaths()
dpspth = DPSPaths()

file_new = pd.read_csv(pth.pali_word_path, sep='\t')

# Construct the path to the second TSV file (file_old)
file_old_path = os.path.join(dpspth.for_compare_dir, 'paliword.tsv')
file_old = pd.read_csv(file_old_path, sep='\t')

# Merge the DataFrames on 'id' and 'pali_1' columns
merged = pd.merge(file_new, file_old, on=['id', 'pali_1'], how='outer', indicator=True)

# Select rows that exist only in the file_new or only in the file_old
mismatched_rows = merged[merged['_merge'] != 'both']

# Save the mismatched rows to a TSV file
output_path = os.path.join(dpspth.for_compare_dir, 'mismatched_rows.tsv')
mismatched_rows[['id', 'pali_1']].to_csv(output_path, sep='\t', index=False)
print(f"Mismatched rows saved to {output_path}")


