#!/usr/bin/env python3
"""
Script to extract gāthā data from BJT JSON file kn-thig.json and save to TSV.
Therīgāthā has Nipāta -> Sutta structure.
"""

import json
from pathlib import Path
import csv
import re
from typing import Any
from natsort import natsorted, ns
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from helpers import clean_string


class GlobalVars:
    """Global variables and config."""

    json_prefix = "kn-thig"
    tsv_filename = "kn9_thig"
    sutta_code_prefix = "thig"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "khuddakanikāyo"

    # file vars
    pth = ProjectPaths()
    json_dir = pth.bjt_roman_json_dir
    json_file_list = natsorted(
        json_dir.glob(f"{json_prefix}.json"),
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
    this_book: str = "therīgāthāpāḷi"
    this_minor_section: str = ""  # corresponds to nipata
    this_vagga: str = ""
    this_sutta: str

    # Counter vars
    this_minor_section_num: int = 0
    this_minor_section_web: int = 0
    this_vagga_num: int = 0
    this_sutta_num: int = 0

    # Track processed sutta numbers to avoid duplicates
    processed_sutta_numbers: set[str] = set()

    # data vars
    data_current_file: list[dict[str, Any]] = []
    data_all: list[dict[str, Any]] = []


def extract_data(g: GlobalVars):
    """Extract gāthā data from a single JSON file."""

    try:
        with open(g.this_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        g.this_filename = data.get("filename", "")
        g.this_book_id = data.get("bookId", "")  # KN books use book_id 28
        g.this_page_offset = data.get("pageOffset", 0)
        pages = data.get("pages", [])

        # reset hierarchy for each file
        g.data_current_file = []

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                # Update hierarchy based on entry type and content
                if entry_type == "centered":
                    if "suttantapiṭake" in entry_text.lower():
                        g.this_piṭaka = clean_string(entry_text)

                    elif entry_level == 1:
                        # Look for sutta numbers - Thig uses "nipāta.sutta" format (e.g. 1. 1.)
                        if re.match(r"^\d+\.\s*\d+", entry_text):
                            # Skip if we've already processed this exact sutta number (avoid Pali/Sinhala duplicates)
                            if entry_text in g.processed_sutta_numbers:
                                continue
                            g.this_sutta_code = f"{g.sutta_code_prefix} {entry_text}"
                            g.processed_sutta_numbers.add(entry_text)
                            sutta_parts = entry_text.rstrip(".").split(".")
                            if len(sutta_parts) >= 2:
                                g.this_minor_section_num = int(sutta_parts[0].strip())
                                g.this_sutta_num = int(sutta_parts[1].strip())

                elif entry_type == "heading":
                    if "therīgāthāpāḷi" in entry_text.lower():
                        g.this_book = clean_string(entry_text)

                    # Check if this is a sutta name heading
                    elif (
                        entry_level == 1
                        and "gāthā" in entry_text
                        and entry_text != "therīgāthāpāḷi"
                    ):
                        g.this_sutta = f"{g.this_sutta_num}. {clean_string(entry_text)}"
                        # Thig doesn't have vaggas, so web code is nipata-sutta
                        g.this_web_code = f"{g.json_prefix}-{g.this_minor_section_web}-{g.this_sutta_num}"

                        if "sumedhātherīgāthā" in entry_text:
                            g.this_sutta_code = f"{g.sutta_code_prefix} 74. 1."

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

                    # Look for nipāta headings like "1. ekakanipāto.", "2. dutiyapāto.", etc.
                    elif "nipāto" in entry_text and "niṭṭhito" not in entry_text:
                        g.this_minor_section = clean_string(entry_text)

                        nipāta_match = re.match(r"^(\d+)", entry_text)

                        if nipāta_match:
                            g.this_minor_section_num = int(nipāta_match.group(1))
                            g.this_minor_section_web += 1

                        if "mahānipāto" in entry_text.lower():
                            g.this_minor_section = f"74. {clean_string(entry_text)}"
                            g.this_minor_section_num = 74
                            g.this_minor_section_web += 1

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
