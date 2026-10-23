"""Shared helpers for the SC sutta extraction: JSON loading and TSV output."""

import csv
import json
from pathlib import Path
from typing import Any

from scripts.suttas.sc.natural_sort import sorted_naturally


def open_sc_json(file_path: Path) -> Any:
    """Open the json file and return the data"""

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_data_dict(
    code: str | None,
    book: str | None,
    vagga: str | None,
    sutta: str | None,
    eng_sutta: str,
    file_path_relative: str,
    data_dict: dict[str, dict[str, str | None]],
) -> dict[str, dict[str, str | None]] | None:
    """Update the data dictionary."""
    if vagga is None:
        vagga = ""
    if sutta is None:
        sutta = ""

    if code and sutta:
        data_dict[code] = {
            "sc_code": code,
            "sc_book": book,
            "sc_vagga": vagga,
            "sc_sutta": sutta,
            "sc_eng_sutta": eng_sutta,
            "sc_blurb": "",
            "sc_card_link": "",
            "sc_pali_link": "",
            "sc_eng_link": "",
            "sc_file_path": file_path_relative,
        }

        return data_dict


def write_sc_data_to_tsv(sc_data: dict[str, dict[str, str | None]]) -> None:
    """Writes the values from sc_data (dict of dicts) to a TSV file."""

    output_file = "scripts/suttas/sc/sc.tsv"
    with open(output_file, "w", newline="", encoding="utf-8") as tsv_file:
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
