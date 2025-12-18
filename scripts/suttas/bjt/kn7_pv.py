#!/usr/bin/env python3
"""
Script to extract vatthu data from BJT JSON file kn-pv.json and save to TSV.
PV has Vagga -> Vatthu structure.
"""

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from helpers import clean_string
from natsort import natsorted, ns

from tools.paths import ProjectPaths
from tools.printer import printer as pr


class GlobalVars:
    """Global variables and config."""

    json_prefix = "kn-pv"
    tsv_filename = "kn7_pv"
    sutta_code_prefix = "pv"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "khuddakanikāyo"

    # file vars
    pth = ProjectPaths()
    json_dir = pth.bjt_roman_json_dir

    json_file_list = natsorted(
        json_dir.glob(f"{json_prefix}*.json"),
        key=lambda x: x.name,
        alg=ns.PATH,
    )

    pr.title(f"extracting from {len(json_file_list)} files starting with {json_prefix}")

    tsv_working_dir = Path("scripts/suttas/bjt")
    tsv_filepath = tsv_working_dir.joinpath(f"{tsv_filename}.tsv")

    # running vars
    this_json_file: Path
    this_sutta_code: str
    this_web_code: str
    this_filename: str
    this_book_id: str
    this_page_num: str
    this_page_offset: str
    this_major_section: str = ""
    this_book: str = "petavatthupāḷi"
    this_minor_section: str = ""  # Empty for PV (doesn't have nipāta structure)
    this_vagga: str = ""
    this_sutta: str

    # counter vars
    this_vagga_num: int = 0
    this_sutta_num: int = 0

    # data vars
    data_current_file: List[Dict[str, Any]] = []
    data_all: List[Dict[str, Any]] = []


def extract_data(g: GlobalVars):
    """Extract vatthu data from a single JSON file."""

    try:
        with open(g.this_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        g.this_filename = data.get("filename", "")
        g.this_book_id = data.get("bookId", "")
        g.this_page_offset = data.get("pageOffset", 0)
        pages = data.get("pages", [])

        # reset hierarchy for each file
        g.data_current_file = []

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                text = entry.get("text", "").strip()
                level = entry.get("level", 0)

                # Update hierarchy based on entry type and content
                if entry_type == "centered":
                    if "suttantapiṭake" in text.lower():
                        g.this_piṭaka = clean_string(text)

                elif entry_type == "heading":
                    if "petavatthupāḷi" in text.lower():
                        g.this_book = clean_string(text)

                    # Look for vagga headings like "1. uragavaggo", "2. cittalatāvaggo", etc.
                    elif re.match(r"^\d+\.\s*\w+.*vaggo?$", text) and level == 2:
                        g.this_vagga = clean_string(text)

                    # Look for vatthu names in heading entries with level 1
                    elif level == 1:
                        # Extract vagga number from current_vagga
                        vagga_match = re.match(r"^(\d+)\.", g.this_vagga)
                        if vagga_match:
                            g.this_vagga_num = int(vagga_match.group(1))
                            # Extract vatthu number by counting existing vatthus in this vagga
                            existing_vatthus = [
                                r
                                for r in g.data_current_file
                                if r["bjt_vagga"] == g.this_vagga
                            ]
                            g.this_sutta_num = len(existing_vatthus) + 1

                            # Generate sutta_code as "{sutta_code_prefix} {vagga_num}. {vatthu_num}."
                            g.this_sutta_code = f"{g.sutta_code_prefix} {g.this_vagga_num}. {g.this_sutta_num}."

                            # Generate web_code as "kn-pv-{vagga_num}-{vatthu_num}"
                            g.this_web_code = (
                                f"{g.json_prefix}-{g.this_vagga_num}-{g.this_sutta_num}"
                            )

                            # Clean up vatthu name
                            g.this_sutta = f"{g.this_sutta_num}. {clean_string(text)}"

                            # Create record
                            record = {
                                "bjt_sutta_code": g.this_sutta_code,
                                "bjt_web_code": g.this_web_code,
                                "bjt_filename": g.this_filename,
                                "bjt_book_id": g.this_book_id,
                                "bjt_page_num": g.this_page_num,
                                "bjt_page_offset": g.this_page_offset,
                                "bjt_piṭaka": g.this_piṭaka,
                                "bjt_nikāya": g.this_nikāya,
                                "bjt_major_section": g.this_major_section,
                                "bjt_book": g.this_book,
                                "bjt_minor_section": g.this_minor_section,
                                "bjt_vagga": g.this_vagga,
                                "bjt_sutta": g.this_sutta,
                            }
                            g.data_current_file.append(record)

    except json.JSONDecodeError as e:
        pr.red(f"Error decoding JSON in {g.this_json_file}: {e}")
    except Exception as e:
        pr.red(f"Error processing {g.this_json_file}: {e}")

    g.data_all.extend(g.data_current_file)


def save_to_tsv(g: GlobalVars):
    """Save data to TSV file."""
    if not g.data_all:
        pr.warning("No data to save")
        return

    # Define exact field order as required
    fieldnames = [
        "bjt_sutta_code",
        "bjt_web_code",
        "bjt_filename",
        "bjt_book_id",
        "bjt_page_num",
        "bjt_page_offset",
        "bjt_piṭaka",
        "bjt_nikāya",
        "bjt_major_section",
        "bjt_book",
        "bjt_minor_section",
        "bjt_vagga",
        "bjt_sutta",
    ]

    with open(g.tsv_filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(g.data_all)
    pr.info(f"saved {len(g.data_all)} records to {g.tsv_filepath}")


def main():
    pr.tic()
    g = GlobalVars()

    if not g.json_file_list:
        pr.warning("No JSON files found")
        return

    # Process each file
    for g.this_json_file in g.json_file_list:
        pr.green(f"processing {g.this_json_file.name}")
        extract_data(g)
        pr.yes(f"extracted {len(g.data_current_file)} records")

    pr.green_title(f"Total extracted: {len(g.data_all)} records")

    # Save to TSV
    save_to_tsv(g)
    pr.toc()


if __name__ == "__main__":
    main()
