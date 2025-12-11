#!/usr/bin/env python3
"""
Script to extract jātaka data from BJT JSON files kn-jat*.json and save to TSV.
Jātaka has Nipāta -> Vagga -> Jātaka structure.
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

    json_prefix = "kn-jat"
    tsv_filename = "kn14_jat"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "khuddakanikāye"
    this_book: str = "jātakapāḷi"

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
    this_major_section: str
    this_minor_section: str
    this_vagga: str
    this_sutta: str

    # counter vars
    this_nipāta_num: int
    this_vagga_num: int
    this_sutta_num: int

    # data vars
    processed_suttas: set[str]
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

        # reset
        g.data_current_file = []
        g.processed_suttas = set()
        g.this_major_section = ""
        # g.this_minor_section = ""
        g.this_vagga = ""
        # g.this_nipāta_num = 0
        g.this_vagga_num = 0

        # Track numbers within each section
        tracker_dict = {}

        for page in pages:
            g.this_page_num = page.get("pageNum", 0)
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "heading":
                    # Look for nipāta headings like "1. ekakanipāto", "2. dukanipāto", etc.
                    if entry_level == 3 and re.match(
                        r"^\d+\.\s*\w+.*nipāt", entry_text
                    ):
                        g.this_minor_section = entry_text
                        nipāta_match = re.match(r"^(\d+)", entry_text)
                        if nipāta_match:
                            g.this_nipāta_num = int(nipāta_match.group(1))
                        g.this_vagga = ""
                        g.this_vagga_num = 0

                    # Special case: Mahānipāto heading (no number)
                    elif entry_level == 3 and entry_text.strip() == "mahānipāto":
                        g.this_minor_section = "22. mahānipāto"
                        g.this_nipāta_num = 22
                        g.this_vagga = ""
                        g.this_vagga_num = 0

                    # Look for vagga headings like "1. apaṇṇakavaggo", "2. sīlavaggo", etc.
                    # But skip if it's a jātaka heading (level 2 jātaka entries in Mahānipāto)
                    elif (
                        entry_level == 2
                        and re.match(r"^\d+\.\s*\w+.*vaggo", entry_text)
                        and "jātakaṃ" not in entry_text
                    ):
                        g.this_vagga = entry_text
                        vagga_match = re.match(r"^(\d+)", entry_text)
                        if vagga_match:
                            g.this_vagga_num = int(vagga_match.group(1))
                            # Initialize counter for this vagga
                            vagga_key = f"{g.this_nipāta_num}-{g.this_vagga_num}"
                            if vagga_key not in tracker_dict:
                                tracker_dict[vagga_key] = 0

                    # Special case: Mahānipāto jātakas (level 2 headings) - CHECK FIRST
                    elif (
                        entry_level == 2
                        and "mahānipāto" in g.this_minor_section.lower()
                        and re.match(r"^\d+\.\s*\w+.*(jātakaṃ|pañho)", entry_text)
                    ):
                        g.this_sutta = clean_string(entry_text)

                        # Check if we've already processed this jātaka name to avoid duplicates
                        # if g.this_sutta not in g.processed_suttas:
                        # Extract jātaka number from heading
                        sutta_match = re.match(r"^(\d+)\.", entry_text)
                        if sutta_match:
                            g.this_sutta_num = int(sutta_match.group(1))

                            # Increment counter for Mahānipāto
                            if "mahānipāto" not in tracker_dict:
                                tracker_dict["mahānipāto"] = 0
                            tracker_dict["mahānipāto"] = tracker_dict["mahānipāto"] + 1
                            sequential_num = tracker_dict["mahānipāto"]

                            # Generate sutta code (two-digit: 22.jātaka)
                            g.this_sutta_code = f"{g.json_prefix} {g.this_nipāta_num} {g.this_sutta_num}."

                            # Generate web code (kn-jat-22-{jātaka})
                            g.this_web_code = f"kn-jat-22-{g.this_sutta_num}"

                            # Create record immediately for Mahānipāto
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
                                "bjt_minor_section": g.this_minor_section,  # nipāta
                                "bjt_vagga": "",  # No vagga for Mahānipāto
                                "bjt_sutta": g.this_sutta,
                            }

                            g.data_current_file.append(record)
                            g.processed_suttas.add(g.this_sutta)
                            continue

                    # Look for jātaka story headings ending in "jātakaṃ."
                    # But skip if it's a Mahānipāto jātaka (handled separately)
                    elif (
                        (entry_level == 1 or entry_level == 2)
                        and re.match(r"^\d+\.\s*\w+.*(jātakaṃ|pañho)", entry_text)
                        and "mahānipāto" not in g.this_minor_section.lower()
                    ):
                        g.this_sutta = clean_string(entry_text)

                        # Check if we've already processed this jātaka name to avoid duplicates
                        # if g.this_sutta not in g.processed_suttas:
                        # Extract jātaka number from the heading
                        sutta_match = re.match(r"^(\d+)\.", entry_text)
                        if sutta_match:
                            g.this_sutta_num = int(sutta_match.group(1))

                            # For nipātas 8+, there are no vaggas, so use nipāta-level counting
                            if g.this_nipāta_num >= 8:
                                # Use nipāta-level counter
                                nipāta_key = f"{g.this_nipāta_num}"
                                if nipāta_key not in tracker_dict:
                                    tracker_dict[nipāta_key] = 0
                                tracker_dict[nipāta_key] = tracker_dict[nipāta_key] + 1
                                sequential_num = tracker_dict[nipāta_key]

                                # Generate sutta code (two-digit: nipāta.jātaka)
                                g.this_sutta_code = f"{g.json_prefix} {g.this_nipāta_num}. {g.this_sutta_num}."

                                # Generate web code (two-digit: kn-jat-{nipāta}-{jātaka})
                                g.this_web_code = (
                                    f"kn-jat-{g.this_nipāta_num}-{sequential_num}"
                                )

                                # Empty vagga field
                                g.this_vagga = ""
                            else:
                                # Earlier nipātas have vaggas
                                vagga_key = f"{g.this_nipāta_num}-{g.this_vagga_num}"
                                tracker_dict[vagga_key] = (
                                    tracker_dict.get(vagga_key, 0) + 1
                                )
                                sequential_num = tracker_dict[vagga_key]

                                # Generate sutta code
                                g.this_sutta_code = f"{g.json_prefix} {g.this_nipāta_num}. {g.this_vagga_num}. {g.this_sutta_num}."

                                # Generate web code
                                g.this_web_code = f"kn-jat-{g.this_nipāta_num}-{g.this_vagga_num}-{sequential_num}"

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
                                "bjt_minor_section": g.this_minor_section,  # nipāta
                                "bjt_vagga": g.this_vagga,
                                "bjt_sutta": g.this_sutta,
                            }

                            g.data_current_file.append(record)
                            g.processed_suttas.add(g.this_sutta)
                        else:
                            print(f"[red]{entry}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {g.this_json_file}: {e}")
    except Exception as e:
        print(f"Error processing {g.this_json_file}: {e}")

    g.data_all.extend(g.data_current_file)


def save_to_tsv(g: GlobalVars):
    """Save data to TSV file."""
    if not g.data_all:
        print("No data to save")
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
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(g.data_all)


def main():
    pr.tic()
    g = GlobalVars()
    if not g.json_file_list:
        print("No JSON files found")
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
