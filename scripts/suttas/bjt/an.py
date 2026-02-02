#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'an-' and save to TSV.
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


def get_book_number(filename: str) -> str:
    """Extract base book number from filename like 'an-1', 'an-2', 'an-3-1'"""
    return filename.replace("an-", "").split("-")[0]


class GlobalVars:
    """Global variables and config."""

    json_prefix = "an-"
    tsv_filename = "an"

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
    this_piṭaka: str
    this_nikāya: str
    this_json_file: Path
    last_json_file: str = ""
    this_sutta_code: str
    this_web_code: str
    this_filename: str
    this_book_id: str
    this_page_num: str
    this_page_offset: str
    this_major_section: str = ""
    this_book: str
    this_minor_section: str = ""  # Paṇṇāsaka
    this_vagga: str
    inner_vagga: str = ""
    this_sutta: str = ""

    # counter vars
    this_major_section_num: int = 0
    this_book_num: int = 0
    this_minor_section_num: int = 0  # paṇṇāsaka
    this_vagga_num: int = 0
    this_sutta_num: int = 0

    # state for web code generation
    last_web_sutta_num: int = 0
    current_vagga_for_web: str = ""

    # data vars
    data_current_file: List[Dict[str, Any]] = []
    data_all: List[Dict[str, Any]] = []
    recorded_suttas: set[str] = set()


def extract_data(g: GlobalVars):
    """Extract sutta data from a single JSON file."""

    try:
        with open(g.this_json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        g.this_filename = data.get("filename", "")
        g.this_book_id = data.get("bookId", "")
        g.this_page_offset = data.get("pageOffset", "")
        pages = data.get("pages", [])

        # Reset hierarchy if we are moving to a new book
        g.data_current_file = []
        g.recorded_suttas = set()
        g.this_minor_section = ""
        g.this_vagga = ""
        g.this_sutta = ""
        g.last_web_sutta_num = 0
        g.current_vagga_for_web = ""

        for page in pages:
            g.this_page_num = str(page.get("pageNum", 0))
            pali_entries = page.get("pali", {}).get("entries", [])

            for i, entry in enumerate(pali_entries):
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                # --------------------------------------------------
                # match four digits 2. 1. 1. 2.
                if (
                    re.match(
                        r"^(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b", entry_text
                    )
                    and entry_level >= 1
                ):
                    sutta_num_match = re.match(
                        r"^(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b", entry_text
                    )
                    if sutta_num_match:
                        g.this_sutta = entry_text
                        g.this_sutta_code = f"{g.tsv_filename} {entry_text}"
                        g.this_book_num = int(sutta_num_match.group(1))
                        g.this_major_section_num = int(sutta_num_match.group(2))
                        g.this_vagga_num = int(sutta_num_match.group(3))
                        g.this_sutta_num = int(sutta_num_match.group(4))

                # --------------------------------------------------
                # match three digits '4. 6. 1.'
                elif (
                    re.match(r"^(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b", entry_text)
                    and entry_level >= 1
                ):
                    sutta_num_match = re.match(
                        r"^(\d+)\b\.*\s*(\d+)\b\.*\s*(\d+)\b", entry_text
                    )
                    if sutta_num_match:
                        g.this_sutta = entry_text
                        g.this_sutta_code = f"{g.tsv_filename} {entry_text}"
                        g.this_book_num = int(sutta_num_match.group(1))
                        g.this_major_section_num = 0
                        g.this_vagga_num = int(sutta_num_match.group(2))
                        g.this_sutta_num = int(sutta_num_match.group(3))

                # --------------------------------------------------
                # match two digits 1-50.
                elif re.match(r"^(\d+)-(\d+)", entry_text) and entry_level >= 1:
                    sutta_num_match = re.match(r"^(\d+)-(\d+)", entry_text)
                    if sutta_num_match:
                        g.this_sutta = (
                            f"{g.tsv_filename} {g.this_vagga_num} {entry_text}"
                        )
                        g.this_sutta_num = int(sutta_num_match.group(1))

                if entry_type == "centered":
                    if "piṭak" in entry_text.lower():
                        g.this_piṭaka = entry_text

                    elif "nikāy" in entry_text.lower() and entry_level == 5:
                        g.this_nikāya = entry_text

                    elif "bhāgo" in entry_text.lower() and 2 <= entry_level == 3:
                        g.this_major_section = entry_text

                    elif re.findall(
                        r"(paṭham|dutiyo|tatiy|catutth|pañcam|chaṭṭh|sattam|aṭṭham|navam|dasam|terasam|paṇṇarasam|soḷasam|niṭṭhit|samatt|samatet|sambuddhassa|paṇṇāsak|vagguddān|vaggo|bhāgo|nipāt|uddānagāthā|^$|\{\*\d*\})|\{\d{1,2}\}$",
                        entry_text,
                    ):
                        pass

                    # else:
                    #     pr.red(f"\n{entry}")

                elif entry_type == "heading":
                    if "nipāto" in entry_text.lower() and entry_level == 4:
                        g.this_book = clean_string(entry_text)
                        g.this_book_num += 1
                        g.this_minor_section = ""  # reset paṇṇāsaka
                        g.this_minor_section_num = 0
                        g.inner_vagga = ""  # reset inner_vagga

                    elif "paṇṇāsak" in entry_text.lower() and entry_level == 3:
                        g.this_minor_section_num += 1
                        clean_entry_text = clean_string(entry_text)
                        if re.findall(r"^\d", clean_entry_text):
                            g.this_minor_section = clean_entry_text
                        else:
                            g.this_minor_section = (
                                f"{g.this_minor_section_num}. {clean_entry_text}"
                            )

                    elif "vaggo" in entry_text.lower() and entry_level == 3:
                        g.this_vagga = clean_string(entry_text)
                        g.inner_vagga = ""  # reset inner_vagga

                    elif "pāḷi" in entry_text.lower() and entry_level == 3:
                        g.this_vagga = clean_string(entry_text)
                        g.inner_vagga = g.this_vagga

                    # --------------------------------------------------
                    # special case of vagga inside pāli
                    elif (
                        re.findall(
                            r"vaggo|papeyyālo|soḷasapasādakaradhammā",
                            entry_text.lower(),
                        )
                        and entry_level == 2
                        and g.inner_vagga
                    ):
                        g.this_vagga = f"{g.inner_vagga}, {clean_string(entry_text)}"

                    # --------------------------------------------------
                    # sometimes vaggas are level 2
                    elif "vaggo" in entry_text.lower() and entry_level == 2:
                        g.this_vagga = clean_string(entry_text)
                        g.inner_vagga = ""  # reset inner_vagga

                    # --------------------------------------------------
                    # special case when vagga is not called vagga
                    elif (
                        re.findall(r"suttāni|rāgādipeyyālaṃ", entry_text.lower())
                        and entry_level == 2
                    ):
                        g.this_vagga = clean_string(entry_text)

                    # --------------------------------------------------
                    # special case when vagga is not called vagga and level 3
                    elif (
                        re.findall(r"suttāni|rāgādipeyyālaṃ", entry_text.lower())
                        and entry_level == 3
                    ):
                        g.this_vagga = clean_string(entry_text)

                    # --------------------------------------------------
                    # suttas
                    elif (
                        re.findall(
                            r"suttaṃ|peyyālaṃ|suttāni|suttādīni|suttādinī", entry_text
                        )
                        and entry_level == 1
                    ):
                        g.this_sutta = f"{g.this_sutta_num}. {clean_string(entry_text)}"

                    # --------------------------------------------------
                    elif (
                        re.findall(r"^\[*\d", entry_text)
                        # and entry_text != g.this_sutta
                    ):
                        pass

                    # --------------------------------------------------
                    else:
                        pr.red(f"\n{entry}")

                    # --------------------------------------------------
                    # make a record
                    if g.this_sutta and g.this_sutta not in g.recorded_suttas:
                        # Check if vagga changed and reset web counter if needed
                        if g.this_vagga != g.current_vagga_for_web:
                            g.last_web_sutta_num = 0
                            g.current_vagga_for_web = g.this_vagga

                        g.last_web_sutta_num += 1
                        # g.this_sutta_code = entry_text.rstrip(".")

                        if g.this_major_section_num:
                            g.this_web_code = f"{g.tsv_filename}-{g.this_book_num}-{g.this_major_section_num}-{g.this_vagga_num}-{g.last_web_sutta_num}"
                        else:
                            g.this_web_code = f"{g.tsv_filename}-{g.this_book_num}-{g.this_vagga_num}-{g.last_web_sutta_num}"

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
                        g.recorded_suttas.add(g.this_sutta)
                        # print(record)

    except json.JSONDecodeError as e:
        pr.red(f"Error decoding JSON in {g.this_json_file}: {e}")
    except Exception as e:
        pr.red(f"Error processing {g.this_json_file}: {e}")

    g.data_all.extend(g.data_current_file)
    g.last_json_file = g.this_json_file.stem


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

# exceptions with 4 numbers
# 16. Ekadhammapāḷi
#   1. Paṭhamovaggo
#       1. 16. 1. 1
#       1. 16. 1. 2-10

# numbering errors
# 6. Chaṭṭhapaṇṇāsakaṃ
# 1. Upasampadāvaggo
# Vaggātireka suttāni
# Bhattuddesaka suttaṃ
# Dutiyabhattuddesakādisuttāni
# Senāsana paññāpakādi suttāni
# Bhikkhusuttaṃ
# Bhikkhunī suttādīni
# Ājīvaka suttaṃ
# Nigaṇṭhasuttādīni
