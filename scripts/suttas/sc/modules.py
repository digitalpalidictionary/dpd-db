import csv
import json

from scripts.suttas.sc.natural_sort import sorted_naturally


def open_sc_json(file_path):
    """Open the json file and return the data"""

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_data_dict(code, book, vagga, sutta, eng_sutta, data_dict):
    """Update the data dictionary."""
    if vagga is None:
        vagga = "-"
    if sutta is None:
        sutta = "-"

    if code and sutta:
        data_dict[code] = {
            "code": code,
            "book": book,
            "vagga": vagga,
            "sutta": sutta,
            "eng_sutta": eng_sutta,
        }
    
        return data_dict


def write_sc_data_to_tsv(sc_data):
    """Writes the values from sc_data (dict of dicts) to a TSV file."""

    output_file = "scripts/suttas/sc/sc.tsv"
    with open(output_file, "w", newline="") as tsv_file:
        writer = csv.writer(tsv_file, delimiter="\t")

        data_list = list(sc_data.values())
        data_list = sorted_naturally(data_list)

        # Extract the header from the first dictionary in the list
        if data_list:
            header = data_list[0].keys()
            writer.writerow(header)

            # Write the rows to the TSV file
            for row in data_list:
                writer.writerow(row.values())

    print(f"tsv file written to {output_file}")