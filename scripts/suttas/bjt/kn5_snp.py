#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files kn-snp*.json and save to TSV.
SNP has Vagga -> Sutta structure.
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


class GlobalVars:
    """Global variables and config."""

    json_prefix = "kn-snp"
    tsv_filename = "kn5_snp"
    sutta_code_prefix = "snp"
    this_piṭaka: str = "suttantapiṭake"  # This gets updated by file content
    this_nikāya: str = "khuddakanikāyo"  # This gets updated by file content

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
    this_book: str = "suttanipātapāḷi"
    this_minor_section: str = ""  # Empty for SNP (doesn't have nipāta structure)
    this_vagga: str = ""
    this_sutta: str

    # counter vars
    this_vagga_num: int = 0
    this_sutta_num: int = 0

    # These need to be reset per file, so will be handled in extract_data
    last_web_sutta_num: int = 0
    current_vagga_for_web: str = ""

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
        g.this_vagga = ""
        g.this_vagga_num = 0
        g.last_web_sutta_num = 0
        g.current_vagga_for_web = ""

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry_index, entry in enumerate(pali_entries):
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "centered":
                    if "nikāye" in entry_text.lower():
                        g.this_piṭaka = clean_string(entry_text)

                    # Look for sutta numbers like "1. 1.", "2. 1.", etc.
                    elif re.match(r"^\d+[\.\-]\s*\d+\.$", entry_text):
                        # Extract sutta numbers
                        sutta_match = re.match(r"^(\d+)\.\s*(\d+)\.$", entry_text)
                        if sutta_match:
                            g.this_vagga_num = int(sutta_match.group(1))
                            g.this_sutta_num = int(sutta_match.group(2))

                            # Check if vagga changed and reset web counter if needed
                            if g.this_vagga != g.current_vagga_for_web:
                                g.last_web_sutta_num = 0
                                g.current_vagga_for_web = g.this_vagga

                            # Always increment by 1 from previous sutta
                            g.last_web_sutta_num += 1

                            # Generate sutta_code as "{sutta_code_prefix} {vagga_num}. {sutta_num}."
                            g.this_sutta_code = f"{g.sutta_code_prefix} {g.this_vagga_num}. {g.this_sutta_num}."

                            # Generate web_code as "kn-snp-{vagga_num}-{web_sutta_num}"
                            g.this_web_code = f"{g.json_prefix}-{g.this_vagga_num}-{g.last_web_sutta_num}"

                            # Look ahead for sutta name in next entry
                            g.this_sutta = entry_text  # fallback to number
                            if entry_index + 1 < len(pali_entries):
                                next_entry = pali_entries[entry_index + 1]
                                if (
                                    next_entry.get("type") == "heading"
                                    and next_entry.get("level") == 1
                                ):
                                    next_text = next_entry.get("text", "").strip()
                                    # Check if it's a sutta name (not another number)
                                    if not re.match(r"^\d+\.\s*\d+\.$", next_text):
                                        # Clean up sutta name
                                        g.this_sutta = f"{g.this_sutta_num}. {clean_string(next_text)}"

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

                elif entry_type == "heading":
                    if "suttanipātapāḷi" in entry_text.lower():
                        g.this_book = clean_string(entry_text)
                    # Special case: vatthugāthā in 5th vagga should be treated as 5. 0.
                    elif (
                        entry_text == "vatthugāthā"
                        and entry_level == 1
                        and "pārāyanavaggo" in g.this_vagga
                    ):
                        g.this_sutta_code = f"{g.sutta_code_prefix} 5. 0."
                        g.this_web_code = f"{g.json_prefix}-5-0"  # Use actual sutta number from sutta_code
                        g.this_sutta = f"0. {entry_text}"

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

                    # Special case: pārāyanānugītigāthā in 5th vagga - should follow the sequence after other suttas in the vagga
                    elif (
                        entry_text == "pārāyanānugītigāthā"
                        and entry_level == 1
                        and "pārāyanavaggo" in g.this_vagga
                    ):
                        sutta_num = 17

                        # Create record with calculated sutta number
                        sutta_code = f"{g.sutta_code_prefix} 5. {sutta_num}."
                        web_code = f"{g.json_prefix}-5-{sutta_num}"
                        g.this_sutta = "17. pārāyanānugītigāthā"

                        record = {
                            "bjt_sutta_code": sutta_code,
                            "bjt_web_code": web_code,
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

                    # Look for vagga headings like "1. uragavaggo", "2. cullavaggo", etc.
                    elif (
                        re.match(r"^\d+\.\s*\w+.*vaggo?$", entry_text)
                        and entry_level == 3
                    ):
                        g.this_vagga = clean_string(entry_text)
                        # Reset counters as new vagga starts
                        g.this_vagga_num = int(
                            re.match(r"^(\d+)\.", entry_text).group(1)
                        )
                        g.last_web_sutta_num = 0
                        g.current_vagga_for_web = g.this_vagga

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

    # Save to TSV
    save_to_tsv(g)
    pr.toc()


if __name__ == "__main__":
    main()
