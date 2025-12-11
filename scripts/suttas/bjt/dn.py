#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'dn-' and save to TSV.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
from natsort import natsorted, ns
from rich import print
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from helpers import clean_string


class GlobalVars:
    """Global variables and config."""

    json_prefix = "dn-"
    tsv_filename = "dn"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "dīghanikāyo"

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
    this_book: str
    this_minor_section: str = ""
    this_vagga: str = ""
    this_sutta: str

    # counter vars
    this_book_num: int = 0
    # this_vagga_num: int = 0
    this_sutta_num: int = 0

    # data vars
    data_current_file: List[Dict[str, Any]] = []
    data_all: List[Dict[str, Any]] = []


def extract_data(g: GlobalVars):
    """Extract sutta data from a single JSON file."""

    try:
        with open(g.this_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        g.this_filename = data.get("filename", "")
        g.this_book_id = data.get("bookId", "")
        g.this_page_offset = data.get("pageOffset", "")
        pages = data.get("pages", [])

        # reset hierarchy for each file
        g.data_current_file = []
        # g.this_book = ""
        # g.this_vagga = ""

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "centered":
                    if "piṭak" in entry_text and entry_level == 2:
                        g.this_piṭaka = clean_string(entry_text)
                    elif "nikāy" in entry_text and entry_level == 5:
                        g.this_nikāya = clean_string(entry_text)
                    elif re.search(r"\d", entry_text):
                        sutta_num_match = re.match(r"^(\d+)\.", entry_text)
                        if sutta_num_match:
                            g.this_sutta_num = int(sutta_num_match.group(1))

                elif entry_type == "heading":
                    # Look for book/vagga headings like "sīlakkhandhavaggo"
                    if "vaggo" in entry_text.lower():
                        g.this_book_num += 1
                        g.this_book = f"{g.this_book_num}. {clean_string(entry_text)}"

                    # Look for sutta patterns in level 1 entries
                    elif entry_level == 3:
                        sutta_match = re.search("suttaṃ", entry_text)
                        if sutta_match:
                            if (
                                not re.match(r"^\d+\.?\s*$", entry_text)
                                and len(entry_text) > 0
                            ):
                                g.this_sutta_code = f"{g.tsv_filename} {g.this_book_num}. {g.this_sutta_num}."
                                g.this_web_code = (
                                    f"dn-{g.this_book_num}-{g.this_sutta_num}"
                                )
                                g.this_sutta = (
                                    f"{g.this_sutta_num}. {clean_string(entry_text)}"
                                )

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
                        else:
                            print(entry)

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

    # Define the exact field order as required
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
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )
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
