#!/usr/bin/env python3

"""removing duplicates from tsv file keeping rows with content in the second column"""

import csv
import os

from dps.tools.paths_dps import DPSPaths    

dpspth = DPSPaths()


def process_tsv(input_file, output_file):
    seen_words = set()
    output_rows = []

    with open(input_file, 'r') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            word = row[0]
            second_col = row[1] if len(row) > 1 else ""

            # If the second column has content, always keep the row
            if second_col.strip():
                output_rows.append(row)  # Keep in the output
            else:
                # For empty second column, keep only the first occurrence of the word
                if word not in seen_words:
                    seen_words.add(word)
                    output_rows.append(row)

    # Write output to a new TSV file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(output_rows)


input_tsv = dpspth.vinaya_tsv_path
output_tsv = os.path.join(dpspth.csv_dps_dir, "vinaya_tsv.tsv")
process_tsv(input_tsv, output_tsv)
