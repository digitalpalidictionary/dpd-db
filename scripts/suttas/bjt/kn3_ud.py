#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON file kn-ud.json and save to TSV.
UD has Vagga -> Sutta structure.
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

    json_prefix = "kn-ud"
    tsv_filename = "kn3_ud"
    sutta_code_prefix = "ud"
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
    this_book: str = "udānapāḷi"
    this_minor_section: str = ""
    this_vagga: str = ""
    this_sutta: str

    # counter vars
    this_vagga_num: int = 0
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

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "centered":
                    if "piṭak" in entry_text:
                        g.this_piṭaka = clean_string(entry_text)
                    elif "nikāy" in entry_text:
                        g.this_nikāya = clean_string(entry_text)

                    # Look for sutta numbers like "1. 1.", "1. 2.", etc.
                    elif re.match(r"^\d+\.\s*\d+\.$", entry_text):
                        # Extract sutta number
                        sutta_match = re.match(r"^(\d+)\.\s*(\d+)\.$", entry_text)
                        if sutta_match:
                            # g.this_vagga_num = int(sutta_match.group(1)) # count vaggas incrementally
                            g.this_sutta_num = int(sutta_match.group(2))

                            # Generate sutta_code as "{vagga_num}. {sutta_num}."
                            g.this_sutta_code = f"{g.sutta_code_prefix} {g.this_vagga_num}. {g.this_sutta_num}."
                            g.this_web_code = (
                                f"{g.json_prefix}-{g.this_vagga_num}-{g.this_sutta_num}"
                            )

                            # Look ahead for sutta name in next entry (hacky but follows existing logic)
                            # In BJT JSON, the sutta name usually follows the number in a heading level 1
                            # We can't easily look ahead here without changing the loop structure significantly
                            # So we set a default and let the next iteration update it if it's a heading
                            g.this_sutta = (
                                f"{g.this_sutta_code} {entry_text}"  # fallback
                            )

                            # But we need to capture the name for the record.
                            # Let's peek into the entries list if possible, or handle it when heading comes.
                            # The logic in previous script was looking ahead.
                            # Here we can check if the NEXT entry is the title.

                            try:
                                current_idx = pali_entries.index(entry)
                                if current_idx + 1 < len(pali_entries):
                                    next_entry = pali_entries[current_idx + 1]
                                    if (
                                        next_entry.get("type") == "heading"
                                        and next_entry.get("level") == 1
                                    ):
                                        next_text = next_entry.get("text", "").strip()
                                        if not re.match(r"^\d+\.\s*\d+\.$", next_text):
                                            g.this_sutta = f"{g.this_sutta_num}. {clean_string(next_text)}"
                            except ValueError:
                                pass  # entry not found in list? should not happen

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
                    if "udānapāḷi" in entry_text.lower():
                        g.this_book = clean_string(entry_text)
                    # Look for vagga headings like "bodhivaggo paṭhamo"
                    elif "vaggo" in entry_text.lower() and entry_level == 2:
                        g.this_vagga_num += 1
                        g.this_vagga = f"{g.this_vagga_num}. {clean_string(entry_text)}"

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
