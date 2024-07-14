#!/usr/bin/env python3
"""Read id_old and id_new from file and replace accordingly in ru and sbs tsvs"""

import json
import csv
import os

from dps.tools.paths_dps import DPSPaths


dpspth = DPSPaths()

dps_ru_path = os.path.join(dpspth.dps_backup_dir, "russian.tsv")
dps_sbs_path = os.path.join(dpspth.dps_backup_dir, "sbs.tsv")
json_path = 'id_dict.json'

def replace_ids_in_file(json_path, tsv_path):
    # Load the ID mapping from the JSON file
    with open(json_path, 'r') as json_file:
        id_mapping = json.load(json_file)

    # Read the TSV file and replace the IDs
    with open(tsv_path, 'r') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        headers = next(reader)  # Read the header row
        rows = list(reader)

    # Replace old IDs with new IDs and collect replacements
    replacements = []
    for row in rows:
        old_id = row[0]
        if old_id in id_mapping:
            new_id = id_mapping[old_id]
            replacements.append((old_id, new_id))
            row[0] = new_id

    # Write the updated rows back to the same TSV file with the required formatting
    with open(tsv_path, 'w', newline='') as tsv_file:
        writer = csv.writer(tsv_file, delimiter='\t', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)  # Write the header row
        writer.writerows(rows)  # Write the data rows

    # Print the replacements
    print(f"ID replacements in {tsv_path}:")
    for old_id, new_id in replacements:
        print(f"{old_id} -> {new_id}")

    print(f"ID replacement complete. Updated file saved as '{tsv_path}'.")


# Call the function for both files
replace_ids_in_file(json_path, dps_ru_path)
replace_ids_in_file(json_path, dps_sbs_path)