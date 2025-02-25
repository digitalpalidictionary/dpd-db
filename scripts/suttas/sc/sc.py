"""
Extract the following data from SC texts
1. Code
2. Sutta name
"""

import json
from pathlib import Path
import re
import csv

from icecream import ic
from tools.paths import ProjectPaths


pth = ProjectPaths()


def open_sc_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_pali(file_path, data):
    data_dict = {}
    folder_name = file_path.parent.name
    
    code = None
    book = None
    vagga_num = None
    vagga = None
    sutta_num = None
    sutta = None

    for line_code, pali_text in data.items():

        if ":0.1" in line_code:
            code = line_code.replace(":0.1", "")
            book = pali_text.strip()
        if ":0.2" in line_code:
            if (
                folder_name.startswith(("an", "sn"))):
                vagga = re.sub(r"\d* \.", "", pali_text.strip())
                vagga_num = re.sub(r" \..+", "", pali_text.strip())
            elif folder_name.startswith(("dn", "mn")):
                sutta = re.sub(r"\d* \.", "", pali_text.strip())
                sutta_num = re.sub(r" \..+", "", pali_text.strip())
        if ":0.3" in line_code:
            if folder_name.startswith(("an", "sn")):
                sutta = re.sub(r"\d* \.", "", pali_text.strip())
                sutta_num = re.sub(r" \..+", "", pali_text.strip())
        if ":1.0" in line_code:
            sutta = re.sub(r"\d* \.", "", pali_text.strip())
            sutta_num = re.sub(r" \..+", "", pali_text.strip())
            
        data_dict[code] = {
            "code": code,
            "book": book,
            "vagga_num": vagga_num,
            "vagga": vagga,
            "sutta_num": sutta_num,
            "sutta": sutta
        }

    return data_dict


def write_sc_data_to_tsv(sc_data):
    """Writes the values from sc_data (dict of dicts) to a TSV file."""

    output_file = "scripts/suttas/sc/sc.tsv"
    with open(output_file, 'w', newline='') as tsv_file:
        writer = csv.writer(tsv_file, delimiter='\t')
        
        # Extract the values (list of dicts) from the sc_data dictionary
        data_list = list(sc_data.values())

        # Extract the header from the first dictionary in the list
        if data_list:
            header = data_list[0].keys()
            writer.writerow(header)

            # Write the rows to the TSV file
            for row in data_list:
                writer.writerow(row.values())
    
    print(f"tsv file written to {output_file}") 


def main():
    sc_data = {}
    base_dir = Path("resources/sc-data/sc_bilara_data/root/pli/ms/sutta")
    file_list = [f for f in base_dir.rglob("*") if f.is_file()]
    for file_path in sorted(file_list):
        json_data = open_sc_json(file_path)
        sc_data.update(extract_pali(file_path, json_data))

    write_sc_data_to_tsv(sc_data)


if __name__ == "__main__":
    main()
