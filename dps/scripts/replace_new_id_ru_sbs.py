#!/usr/bin/env python3

"""replacing id in ru and sbs backup files according to additions.csv"""

import sys
import os

from tools.paths import ProjectPaths
from tools.tsv_read_write import read_tsv_dot_dict, write_tsv_dot_dict
from dps.tools.paths_dps import DPSPaths
from tools.tic_toc import tic, toc


pth = ProjectPaths()


def main():
    tic()
    print("[bright_yellow]replacing id in ru and sbs backup files according to additions.csv")

    pth = ProjectPaths()
    dpspth = DPSPaths()

    if pth.dpd_db_path.exists():
        pth.dpd_db_path.unlink()

    for p in [
        pth.russian_path,
        pth.sbs_path
    ]:
        if not p.exists():
            print(f"[bright_red]TSV backup file does not exist: {p}")
            sys.exit(1)

    additions_file_path = os.path.join(pth.temp_dir, 'additions.tsv')

    # Create a temporary file path within the temporary directory
    output_file_path_ru = os.path.join(pth.temp_dir, 'ru_temp.tsv')
    output_file_path_sbs = os.path.join(pth.temp_dir, 'sbs_temp.tsv')

    # Replace values and save the updated data
    replace_values_and_save(pth.russian_path, additions_file_path, output_file_path_ru)
    replace_values_and_save(pth.sbs_path, additions_file_path, output_file_path_sbs)

    toc()


def replace_values_and_save(input_path, additions_file_path, output_file_path):
    # Read the TSV files as dotdict objects
    input_data = read_tsv_dot_dict(input_path)
    additions_data = read_tsv_dot_dict(additions_file_path)

    # Create a mapping from old_id to new_id
    id_mapping = {entry.old_id: entry.new_id for entry in additions_data}

    # Replace values in the input_data using the id_mapping
    for entry in input_data:
        if entry.id in id_mapping:
            entry.id = id_mapping[entry.id]

    # Save the updated data to a new TSV file
    write_tsv_dot_dict(output_file_path, input_data)
