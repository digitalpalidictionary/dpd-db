#!/usr/bin/env python3

"""replace example info in sbs backup according to sbs_correction tsv and mark replaced rows as "proccesed"""

from rich.console import Console

import csv
import os

from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths  

console = Console()

pth = ProjectPaths()
dpspth = DPSPaths()


def process_tsv():
    tic()
    console.print("[bold yellow]replacing sbs_example in backup tsv")
    corrections_file = dpspth.sbs_example_corrections

    # Load and process the corrections file
    with open(corrections_file, mode='r+', newline='', encoding='utf-8') as corrections:
        corrections_reader = csv.DictReader(corrections, delimiter='\t')
        corrections_data = list(corrections_reader)
        corrections_header = corrections_reader.fieldnames

        # Load the existing `sbs.tsv` file data
        with open(pth.sbs_path, mode='r', newline='', encoding='utf-8') as sbs_file:
            sbs_reader = csv.DictReader(sbs_file, delimiter='\t')
            sbs_data = {row['id']: row for row in sbs_reader}
            sbs_header = sbs_reader.fieldnames

        # Iterate through each row in the corrections file
        for correction_row in corrections_data:
            id_ = correction_row['id']

            # Check for `n` in any correct_{i} fields and copy the corresponding example fields
            for set_number in range(1, 5):
                correct_key = f'correct_{set_number}'
                if correction_row[correct_key] == 'n':
                    # Fields to be copied
                    fields_to_copy = [
                        f'sbs_source_{set_number}',
                        f'sbs_sutta_{set_number}',
                        f'sbs_example_{set_number}',
                        correct_key,
                        f'sbs_chant_pali_{set_number}',
                        f'sbs_chant_eng_{set_number}',
                        f'sbs_chapter_{set_number}',
                    ]
                    
                    if id_ in sbs_data:
                        # Update the `sbs.tsv` data with the fields from the corrections file
                        for field in fields_to_copy:
                            sbs_data[id_][field] = correction_row[field]

                        # Change "n" to "p" in the corrections file
                        correction_row[correct_key] = 'p'

        console.print("[bold green]writing updated SBS table updated")\
        # Write the updated data back to the `sbs.tsv`
        with open(pth.sbs_path, mode='w', newline='', encoding='utf-8') as sbs_file_output:
            csvwriter = csv.writer(
                sbs_file_output, delimiter="\t", quotechar='"', quoting=csv.QUOTE_ALL)
            # Assuming sbs_model is the ORM model class with a __mapper__ attribute
            csvwriter.writerow(sbs_header)
            for row in sbs_data.values():
                csvwriter.writerow([row[col] for col in sbs_header])

        console.print("[bold green]writing updated correction tsv")
        # Write the updated data back to the corrections file
        corrections.seek(0)  # Rewind the corrections file to the beginning
        corrections_writer = csv.DictWriter(corrections, fieldnames=corrections_header, delimiter='\t')
        corrections_writer.writeheader()
        for row in corrections_data:
            corrections_writer.writerow(row)
        corrections.truncate()  # Cut off any remaining old data if file shrinks
    
    toc()


process_tsv()