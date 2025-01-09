#!/usr/bin/env python3

"""find changed lemma_1 from last check date, and save it into csv for compare what has been changed"""

import os

import pandas as pd

from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

pth = ProjectPaths()
dpspth = DPSPaths()

file_new = pd.read_csv(pth.pali_word_path, sep='\t', low_memory=False)

# Construct the path to the second TSV file (file_old)
file_old_path = os.path.join(dpspth.for_compare_dir, 'dpd_headwords.tsv')
file_old = pd.read_csv(file_old_path, sep='\t', low_memory=False)

# Merge the DataFrames on 'id' and 'lemma_1' columns
merged = pd.merge(file_new, file_old, on=['id', 'lemma_1'], how='outer', indicator=True)

# Merge the DataFrames on 'id' and 'note' columns
merged_notes = pd.merge(file_new, file_old, on=['id', 'notes'], how='outer', indicator=True)

# Select rows that exist only in the file_new or only in the file_old
mismatched_rows = merged[merged['_merge'] != 'both']
mismatched_notes_rows = merged_notes[merged_notes['_merge'] != 'both']

# Read the backup_ru file into a DataFrame
backup_ru = pd.read_csv(pth.russian_path, sep='\t')

backup_dps_ru_pth = os.path.join(dpspth.dps_backup_dir, 'russian.tsv')
backup_dps_ru = pd.read_csv(backup_dps_ru_pth, sep='\t', low_memory=False)

# Step 1: Combine the IDs from both DataFrames
all_ids = pd.concat([backup_ru['id'], backup_dps_ru['id']])

# Step 2: Identify IDs that are unique to each DataFrame
unique_to_ru = backup_ru[~backup_ru['id'].isin(backup_dps_ru['id'])]['id']
unique_to_dps = backup_dps_ru[~backup_dps_ru['id'].isin(backup_ru['id'])]['id']

# Step 3: Combine these unique IDs into a single list
unique_ids = pd.concat([unique_to_ru, unique_to_dps])

# Step 4: Save this list of unique IDs into a TSV file
unique_ids.to_csv(os.path.join(dpspth.for_compare_dir, 'ru_unique_ids.tsv'), sep='\t', index=False)

print(f"{len(unique_ids)} IDs that do not exist in both backup_ru and backup_dps_ru saved to unique_ids.tsv")

# Merge the mismatched_rows DataFrame with the backup_ru DataFrame on 'id'
merged_with_ru = pd.merge(mismatched_rows, backup_ru, on='id', how='inner')
merged_notes_with_ru = pd.merge(mismatched_notes_rows, backup_ru, on='id', how='inner')

# Remove duplicates based on 'id'
merged_with_ru = merged_with_ru.drop_duplicates(subset='id')
merged_notes_with_ru = merged_notes_with_ru.drop_duplicates(subset='id')

# Filter the rows that have ru_meaning
filtered_rows = merged_with_ru[merged_with_ru['ru_meaning'].notna()] #type: ignore
filtered_rows_notes = merged_notes_with_ru[merged_notes_with_ru['ru_notes'].notna()] #type: ignore


# Save the mismatched rows to a TSV file
output_path = os.path.join(dpspth.for_compare_dir, 'added_another_meaning.tsv')
notes_output_path = os.path.join(dpspth.for_compare_dir, 'changed_notes.tsv')
# mismatched_rows[['id', 'lemma_1']].to_csv(output_path, sep='\t', index=False)
# print(f"Mismatched rows saved to {output_path}")

# Save the filtered rows to a TSV file
filtered_rows[['id', 'lemma_1']].to_csv(output_path, sep='\t', index=False)
filtered_rows_notes.to_csv(notes_output_path, sep='\t', index=False)
print(f"{len(filtered_rows)} words which have added new meaning saved into {output_path}")
print(f"{len(filtered_rows_notes)} words which have changed notes saved into {notes_output_path}")

# Save just id for gui
# filtered_rows[['id']].to_csv(dpspth.id_temp_list_path, sep='\t', index=False)
# print(f"id list saved to {dpspth.id_temp_list_path}")





