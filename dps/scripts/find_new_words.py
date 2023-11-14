#!/usr/bin/env python3

"""Filter the list of words that have acquired an additional English meaning or have had their meanings separated."""

from rich.console import Console

import pandas as pd
import os

from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH

console = Console()

tic()

paliword_original = os.path.join(DPSPTH.backup_for_compare_dir, "paliword.tsv")
russian_original = os.path.join(DPSPTH.backup_for_compare_dir, "russian.tsv")

paliword_new = PTH.pali_word_path

# First part
# 1. Read csv pali_word.csv
pali_word = pd.read_csv(paliword_original, sep='\t', low_memory=False)

# 2. Read csv russian.csv
russian = pd.read_csv(russian_original, sep='\t')

# 3. Merge them knowing that they have column 'id' as overlap
merged_df = pd.merge(pali_word, russian, on='id', how='inner')

# 4. From merged df filter those which have column ru_meaning not empty
merged_df = merged_df[merged_df['ru_meaning'].notna()]

# 5. From filtered df, take only column pali_1
df_original = merged_df['pali_1']

# 6. Remove " /d" [space + digit] from this column, including 2 digits or digits with dot
df_original = df_original.str.replace(r'\s\d+(\.\d{1,2})?|\s\d{1,2}', '', regex=True)

# Second part
# 1. Read csv pali_word_2.csv
pali_word_2 = pd.read_csv(paliword_new, sep='\t', low_memory=False)

# 2. Filter rows which are in pali_word_2.csv but not in pali_word.csv
filtered_pali_word_2 = pali_word_2[~pali_word_2['id'].isin(pali_word['id'])]

# 3. Take from filtered df only column pali_1
df_new = filtered_pali_word_2['pali_1']

# 4. Remove " /d" [space + digit] from this column, including 2 digits or digits with dot
df_new = df_new.str.replace(r'\s\d+(\.\d{1,2})?|\s\d{1,2}', '', regex=True)

# Find overlap between df_original and df_new
overlap = df_original[df_original.isin(df_new)]

# Remove duplicates
overlap = overlap.drop_duplicates()

# Save the overlap as a CSV
overlap.to_csv(DPSPTH.new_words_path, index=False)

toc()

print("Display words")
print("")

# Display words one by one
remaining_words = overlap.tolist()
total_words = len(remaining_words)
word_count = 0

while remaining_words:
    # Wait for user to press Enter to see the next word
    input("Press Enter to see the next word...")

    # Get and print the next word
    word = remaining_words.pop(0)
    word_count += 1
    print(f"Word {word_count}: {word}")
    print(f"Words left: {total_words - word_count}")

print("No words left")