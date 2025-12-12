#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'sn-' and save to TSV.
This is a simplified version based on the mn.py structure.
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

    json_prefix = "sn-"
    tsv_filename = "sn"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "saṃyuttanikāyo"

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
    this_major_section: str  # For Mahāvagga
    this_book: str  # For Saṃyutta
    this_minor_section: str = ""  # Unused in SN
    this_vagga: str  # For Vagga within Saṃyutta
    this_vagga_special: str = ""
    this_sutta: str

    # counter vars
    this_major_section_num: int = 0
    this_book_num: int = 0
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

        # Reset hierarchy for each file
        g.data_current_file = []
        # g.this_major_section = ""
        # g.this_book = ""
        g.this_vagga = ""
        g.this_sutta = ""

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "centered":
                    if "piṭak" in entry_text.lower() and entry_level == 3:
                        g.this_piṭaka = entry_text

                    elif "nikāy" in entry_text.lower() and entry_level == 5:
                        g.this_nikāya = entry_text

                    elif re.search(r"\d", entry_text) and entry_level >= 1:
                        sutta_num_match = re.match(
                            r"^(\d+)\.*\s*(\d+)\.*\s*(\d+)\.*\s*", entry_text
                        )
                        if sutta_num_match:
                            g.this_sutta_code = f"{g.tsv_filename} {g.this_major_section_num}. {entry_text}"
                            # g.this_book_num = int(sutta_num_match.group(1))
                            g.this_vagga_num = int(sutta_num_match.group(2))
                            g.this_sutta_num = int(sutta_num_match.group(3))

                elif entry_type == "heading":
                    # 5 main vaggas
                    if "vaggo" in entry_text.lower() and entry_level >= 4:
                        g.this_major_section_num += 1
                        g.this_major_section = (
                            f"{g.this_major_section_num}. {clean_string(entry_text)}"
                        )
                        g.this_book_num = 0  # reset saṃyutta

                    elif "saṃyutta" in entry_text.lower():  # and entry_level == 3:
                        g.this_book_num += 1
                        g.this_book = clean_string(entry_text)  # Saṃyutta
                        g.this_vagga_num = 0  # reset vagga
                        g.this_minor_section = ""  # reset paṇṇāsaka

                    elif "paṇṇāsak" in entry_text.lower() and entry_level == 3:
                        g.this_minor_section = clean_string(entry_text)

                    # 9. Antarapeyyālo is a special case where it has the position of vagga,
                    # but has multiple vaggas inside of it. The solutions is to combine the
                    # Antarapeyyālo with the vagga name. There are thus special conditions within
                    # vagga and sutta to handle it.
                    elif "antarapeyyālo" in entry_text.lower():
                        g.this_vagga_special = clean_string(entry_text)

                    # vaggas
                    elif (
                        re.findall(
                            "vaggo|pañcakaṃ|peyyālo",
                            entry_text.lower(),
                        )
                        and 2 <= entry_level <= 3
                    ):
                        # g.this_vagga_num += 1
                        if g.this_vagga_special:
                            g.this_vagga = (
                                f"{g.this_vagga_special}, {clean_string(entry_text)}"
                            )
                        else:
                            g.this_vagga = clean_string(entry_text)  # Vagga

                        # turn off special vagga
                        if "appamādavaggo" in entry_text.lower():
                            g.this_vagga_special = ""

                    # suttas
                    elif re.findall(
                        "suttaṃ|suttāni|suvaṇṇanikkhasuttādiaṭṭhakaṃ|dutiyasakkasūttaṃ|pitusuttādichakkaṃ",
                        entry_text,
                    ):
                        g.this_sutta = f"{g.this_sutta_num}. {clean_string(entry_text)}"
                        if g.this_vagga_special:
                            g.this_web_code = f"{g.tsv_filename}-{g.this_major_section_num}-{g.this_book_num}-9-{g.this_vagga_num}-{g.this_sutta_num}"
                        elif g.this_vagga_num:
                            g.this_web_code = f"{g.tsv_filename}-{g.this_major_section_num}-{g.this_book_num}-{g.this_vagga_num}-{g.this_sutta_num}"
                        else:
                            g.this_web_code = f"{g.tsv_filename}-{g.this_major_section_num}-{g.this_book_num}-{g.this_sutta_num}"

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
                        pr.red(f"{entry}")

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

    save_to_tsv(g)
    pr.toc()


if __name__ == "__main__":
    main()
