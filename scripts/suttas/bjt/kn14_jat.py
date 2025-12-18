#!/usr/bin/env python3
"""
Script to extract jātaka data from BJT JSON files kn-jat*.json and save to TSV.
Jātaka has Nipāta -> Vagga -> Jātaka structure (early nipātas)
or Nipāta -> Jātaka structure (later nipātas and Mahānipāto).
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

    json_prefix = "kn-jat"
    tsv_filename = "kn14_jat"
    sutta_code_prefix = "jat"
    this_piṭaka: str = "suttantapiṭake"
    this_nikāya: str = "khuddakanikāyo"
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
    this_page_offset: int
    this_major_section: str = ""
    this_minor_section: str = ""  # nipāta
    this_vagga: str = ""
    this_sutta: str

    # counter vars
    this_minor_section_num: int = 0
    this_vagga_num: int = 0
    this_sutta_num: int = 0

    # Track processed suttas
    processed_suttas: set[str] = set()

    # data vars
    data_current_file: list[dict[str, Any]] = []
    data_all: list[dict[str, Any]] = []


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
            g.this_page_num = str(page.get("pageNum", ""))
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                entry_text = entry.get("text", "").strip()
                entry_level = entry.get("level", 0)

                if entry_type == "heading":
                    if "mahānipāto" in entry_text.lower():
                        g.this_minor_section = "22. mahānipāto"
                        g.this_minor_section_num = 22
                        g.this_vagga = ""
                        g.this_vagga_num = 0

                    elif "nipāt" in entry_text and entry_level != 1:
                        g.this_minor_section = clean_string(entry_text)
                        nipāta_match = re.match(r"^(\d+)", entry_text)
                        if nipāta_match:
                            g.this_minor_section_num = int(nipāta_match.group(1))
                        g.this_vagga = ""
                        g.this_vagga_num = 0

                    elif "vaggo" in entry_text.lower():
                        g.this_vagga = clean_string(entry_text)
                        vagga_match = re.match(r"^(\d+)", entry_text)
                        if vagga_match:
                            g.this_vagga_num = int(vagga_match.group(1))

                    elif "jātakaṃ" in entry_text or "pañho" in entry_text:
                        sutta_match = re.match(r"^(\d+)\.", entry_text)
                        if sutta_match:
                            g.this_sutta_num = int(sutta_match.group(1))

                            g.this_sutta = clean_string(entry_text)

                            if g.this_vagga_num == 0:
                                g.this_web_code = f"{g.json_prefix}-{g.this_minor_section_num}-{g.this_sutta_num}"
                                g.this_sutta_code = f"{g.sutta_code_prefix} {g.this_minor_section_num}. {g.this_sutta_num}."
                            else:
                                g.this_web_code = f"{g.json_prefix}-{g.this_minor_section_num}-{g.this_vagga_num}-{g.this_sutta_num}"
                                g.this_sutta_code = f"{g.sutta_code_prefix} {g.this_minor_section_num}. {g.this_vagga_num}. {g.this_sutta_num}."

                            g.processed_suttas.add(g.this_sutta_code)

                            # Generate Web Code
                            # Logic:
                            # 1. Mahānipāto (22) -> kn-jat-22-{sutta_num}
                            # 2. Early Nipātas (with Vaggas) -> kn-jat-{nipāta}-{vagga}-{seq_in_vagga} ??
                            #    Wait, standard convention usually ignores vagga in web code if sequential?
                            #    Let's check `kn8_thag` style: prefix-nip-vag-sut OR prefix-nip-sut.
                            #    Jatakas are globally numbered (1-547).
                            #    Maybe `kn-jat-{nipāta}-{sutta_num}`? Or `kn-jat-{nipāta}-{sutta_num}`?
                            #    Let's stick to the previous script's logic if it makes sense,
                            #    or the standard `kn-jat-{nipāta}-{sutta}` if unique within nipāta.
                            #    Actually, `kn14_jat.py` old version had complex counter logic.
                            #    Let's try to simplify. Jataka numbers do NOT reset. They go 1..547.
                            #    So `kn-jat-{nipāta}-{sutta_num}` is redundant but descriptive.
                            #    However, BJT web identifiers might expect the section-based index.

                            # Let's use a simpler counter strategy:
                            # If Vagga exists: kn-jat-{nipāta}-{vagga}-{sutta_num} (or sequential index?)
                            # The old script calculated `sequential_num` within the vagga.
                            # Let's try to replicate "sequential index within parent container".

                            # seq_num = 0

                            # if g.this_vagga:
                            #     vagga_key = f"{g.this_minor_section_num}-{g.this_vagga_num}"
                            #     g.vagga_counter[vagga_key] = (
                            #         g.vagga_counter.get(vagga_key, 0) + 1
                            #     )
                            #     seq_num = g.vagga_counter[vagga_key]
                            #     g.this_web_code = f"{g.json_prefix}-{g.this_minor_section_num}-{g.this_vagga_num}-{seq_num}"

                            #     # Sutta code with 3 parts
                            #     g.this_sutta_code = f"{g.json_prefix} {g.this_minor_section_num}. {g.this_vagga_num}. {g.this_sutta_num}."

                            # else:
                            #     # No vagga (Mahānipāto or mid-range)
                            #     nip_key = g.this_minor_section_num
                            #     g.nipāta_sutta_counter[nip_key] = (
                            #         g.nipāta_sutta_counter.get(nip_key, 0) + 1
                            #     )
                            #     seq_num = g.nipāta_sutta_counter[nip_key]
                            #     # Web code: kn-jat-{nipāta}-{seq_num} ?? Or {sutta_num}?
                            #     # Old script used {sequential_num}. Let's stick to that to be safe.
                            #     g.this_web_code = (
                            #         f"{g.json_prefix}-{g.this_minor_section_num}-{seq_num}"
                            #     )

                            #     # Sutta code with 2 parts
                            #     g.this_sutta_code = f"{g.json_prefix} {g.this_minor_section_num}. {g.this_sutta_num}."

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
        pr.yes(f"extracted {len(g.data_current_file)} records")

    save_to_tsv(g)
    pr.toc()


if __name__ == "__main__":
    main()
