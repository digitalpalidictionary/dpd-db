#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'an-' and save to TSV.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
from natsort import natsorted, ns
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from helpers import clean_string


def get_book_number(filename: str) -> str:
    """Extract base book number from filename like 'an-1', 'an-2', 'an-3-1'"""
    return filename.replace('an-', '').split('-')[0]


class GlobalVars:
    """Global variables and config."""

    json_prefix = "an-"
    tsv_filename = "an"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "aṅguttaranikāyo"

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
    this_page_offset: str = "0"
    this_major_section: str = ""
    this_book: str = "" # Nipāta
    this_minor_section: str = "" # Paṇṇāsaka
    this_vagga: str = ""
    this_sutta: str
    last_filename: str = ""

    # state for web code generation
    last_web_sutta_num: int = 0
    current_vagga_for_web: str = ""

    # data vars
    data_current_file: List[Dict[str, Any]] = []
    data_all: List[Dict[str, Any]] = []

    book_id_map = {
        "an-1": "22", "an-2": "22", "an-3": "22", "an-4": "23",
        "an-5": "24", "an-6": "25", "an-7": "25", "an-8": "26",
        "an-9": "26", "an-10": "27", "an-11": "27",
    }


def extract_data(g: GlobalVars):
    """Extract sutta data from a single JSON file."""
    g.data_current_file = []

    # Reset hierarchy if we are moving to a new book (e.g. from an-3 to an-4)
    if g.last_filename:
        current_book_num = get_book_number(g.this_json_file.stem)
        last_book_num = get_book_number(g.last_filename)
        if current_book_num != last_book_num:
            g.this_book = ""
            g.this_minor_section = ""
            g.this_vagga = ""
            g.last_web_sutta_num = 0
            g.current_vagga_for_web = ""


    try:
        with open(g.this_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        g.this_filename = data.get("filename", "")
        g.this_book_id = g.book_id_map.get(g.this_filename, "22")

        pages = data.get("pages", [])

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for i, entry in enumerate(pali_entries):
                entry_type = entry.get("type", "")
                text = entry.get("text", "").strip()
                level = entry.get("level", 0)

                # Update hierarchy
                if "nipāto" in text.lower() and (entry_type == "centered" or (entry_type == "heading" and level < 3)):
                    g.this_book = clean_string(text)
                elif "paṇṇāsako" in text.lower() and (entry_type == "centered" or entry_type == "heading") and level <= 3:
                    g.this_minor_section = clean_string(text)
                elif "vaggo" in text.lower() and (entry_type == "centered" or entry_type == "heading") and level <= 3:
                    g.this_vagga = clean_string(text)

                # Find sutta
                sutta_code_match = re.match(r"^\d+\.\s*\d+\.\s*\d+", text)
                if sutta_code_match and (entry_type == "centered" or entry_type == "heading") and level == 1:
                    sutta_parts = text.rstrip(".").split(".")
                    if len(sutta_parts) < 3:
                        continue

                    try:
                        nipata_num = int(sutta_parts[0].strip())
                        vagga_num = int(sutta_parts[1].strip())

                        # Check if vagga changed and reset web counter if needed
                        if g.this_vagga != g.current_vagga_for_web:
                            g.last_web_sutta_num = 0
                            g.current_vagga_for_web = g.this_vagga

                        g.last_web_sutta_num += 1
                        g.this_sutta_code = text.rstrip(".")
                        g.this_web_code = f"an-{nipata_num}-{vagga_num}-{g.last_web_sutta_num}"

                        # Look ahead for sutta name
                        g.this_sutta = text  # fallback to number
                        if i + 1 < len(pali_entries):
                            next_entry = pali_entries[i + 1]
                            if next_entry.get("type") == "heading" and next_entry.get("level") == 1:
                                next_text = next_entry.get("text", "").strip()
                                if not re.match(r"^\d+\.\s*\d+\.\s*\d+", next_text):
                                    g.this_sutta = clean_string(next_text).replace("vaggo", "").strip()

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

                    except (ValueError, IndexError):
                        continue

    except json.JSONDecodeError as e:
        pr.red(f"Error decoding JSON in {g.this_json_file}: {e}")
    except Exception as e:
        pr.red(f"Error processing {g.this_json_file}: {e}")

    g.data_all.extend(g.data_current_file)
    g.last_filename = g.this_json_file.stem


def save_to_tsv(g: GlobalVars):
    """Save data to TSV file."""
    if not g.data_all:
        pr.warning("No data to save")
        return

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

    for g.this_json_file in g.json_file_list:
        pr.green(f"processing {g.this_json_file.name}")
        extract_data(g)
        pr.yes(len(g.data_current_file))

    pr.green_title(f"total: {len(g.data_all)}")
    save_to_tsv(g)
    pr.toc()


if __name__ == "__main__":
    main()