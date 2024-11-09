#!/usr/bin/env python3
"""
replace new id with old id according to additions.tsv in the backup files sbs and ru
"""

import csv

from tools.paths import ProjectPaths

pth = ProjectPaths()

def replace_ids(pth: ProjectPaths, custom_path: str = ""):
    # Read additions.tsv and create a dictionary with new_id and id
    additions_dict = {}
    with open(pth.additions_tsv_path, newline='', encoding='utf-8') as additions_file:
        reader = csv.DictReader(additions_file, delimiter='\t')
        for row in reader:
            id_clean = row['id'].strip().strip('"')  # Clean quotes for matching
            new_id_clean = row['new_id'].strip().strip('"')  # Clean quotes for matching
            additions_dict[id_clean] = new_id_clean

    # Debugging: print out the additions_dict to verify its content
    # print(f"Additions Dictionary: {additions_dict}")

    # Function to process a TSV file
    def process_file(file_path):
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            lines = file.readlines()

        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            for line in lines:
                # Preserve the original line formatting
                # original_line = line.strip()

                # Split by tabs but preserve quoted parts properly
                columns = line.strip().split('\t')

                # Clean the first column ID for matching
                id_to_replace = columns[0].strip().strip('"')  # Clean quotes for matching

                # Debugging: Print the ID being checked
                # print(f"Checking ID: {repr(id_to_replace)}")

                # Replace only if ID is found in the additions dictionary
                if id_to_replace in additions_dict:
                    new_id = additions_dict[id_to_replace]
                    if new_id:
                        print(f"Found match: Replacing {repr(id_to_replace)} with {repr(new_id)}")

                        # Replace the first column (ID) and keep the rest of the row intact
                        columns[0] = f'"{new_id}"'
                    else:
                        print(f"word not added yet: {repr(id_to_replace)}")

                # Join the columns and write back the line, preserving original formatting
                file.write('\t'.join(columns) + '\n')

    # Use custom_path if provided, otherwise use default paths
    russian_path = custom_path if custom_path else pth.russian_path
    sbs_path = custom_path if custom_path else pth.sbs_path

    process_file(russian_path)
    print("Russian replacements done successfully.")

    process_file(sbs_path)
    print("SBS replacements done successfully.")

replace_ids(pth)
