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


def clean_jātaka_name(text: str) -> str:
    """Clean jātaka name by removing brackets, curly braces, trailing fullstops, and footnote markers."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    cleaned = cleaned.rstrip(".")  # Remove trailing fullstops
    return cleaned.strip()


def extract_jātaka_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract jātaka data from kn-jat*.json files."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")
        book_id = 28  # KN books use book_id 28

        # Get pages
        pages = data.get("pages", [])

        current_piṭaka = "suttantapiṭake"
        current_nikaya = "khuddakanikāye"
        current_book = "jātakapāḷi"
        current_nipāta = ""
        current_vagga = ""

        nipāta_num = 0
        vagga_num = 0

        # Track jātaka numbers within each section
        vagga_jataka_counter = {}

        # Track processed jātaka names to avoid duplicates
        processed_jātaka_names = set()

        for page in pages:
            page_num = page.get("pageNum", 0)

            # Get Pali entries
            pali_entries = page.get("pali", {}).get("entries", [])

            for entry in pali_entries:
                entry_type = entry.get("type", "")
                text = entry.get("text", "").strip()
                level = entry.get("level", 0)

                # Update hierarchy based on entry type and content
                if entry_type == "centered":
                    if "suttantapiṭake" in text.lower():
                        current_piṭaka = "suttantapiṭake"
                    elif "khuddakanikāye" in text.lower():
                        current_nikaya = "khuddakanikāye"

                elif entry_type == "heading":
                    if "jātakapāḷi" in text.lower():
                        current_book = text

                    # Look for nipāta headings like "1. ekakanipāto", "2. dukanipāto", etc.
                    elif level == 3 and re.match(r"^\d+\.\s*\w+.*nipāt", text):
                        current_nipāta = text
                        nipāta_match = re.match(r"^(\d+)", text)
                        if nipāta_match:
                            nipāta_num = int(nipāta_match.group(1))
                        current_vagga = ""
                        vagga_num = 0

                    # Special case: Mahānipāto heading (no number)
                    elif level == 3 and text.strip() == "mahānipāto":
                        current_nipāta = text
                        nipāta_num = 22  # Set to 22 for Mahānipāto
                        current_vagga = ""
                        vagga_num = 0

                    # Look for vagga headings like "1. apaṇṇakavaggo", "2. sīlavaggo", etc.
                    # But skip if it's a jātaka heading (level 2 jātaka entries in Mahānipāto)
                    elif (
                        level == 2
                        and re.match(r"^\d+\.\s*\w+.*vaggo", text)
                        and "jātakaṃ" not in text
                    ):
                        current_vagga = text
                        vagga_match = re.match(r"^(\d+)", text)
                        if vagga_match:
                            vagga_num = int(vagga_match.group(1))
                            # Initialize counter for this vagga
                            vagga_key = f"{nipāta_num}-{vagga_num}"
                            if vagga_key not in vagga_jataka_counter:
                                vagga_jataka_counter[vagga_key] = 0

                    # Special case: Mahānipāto jātakas (level 2 headings) - CHECK FIRST
                    elif (
                        level == 2
                        and "mahānipāto" in current_nipāta.lower()
                        and re.match(r"^\d+\.\s*\w+.*jātakaṃ", text)
                    ):
                        jātaka_name = clean_jātaka_name(text)

                        # Check if we've already processed this jātaka name to avoid duplicates
                        if jātaka_name not in processed_jātaka_names:
                            # Extract jātaka number from heading
                            jātaka_match = re.match(r"^(\d+)\.", text)
                            if jātaka_match:
                                jātaka_num = int(jātaka_match.group(1))

                                # Increment counter for Mahānipāto
                                if "mahānipāto" not in vagga_jataka_counter:
                                    vagga_jataka_counter["mahānipāto"] = 0
                                vagga_jataka_counter["mahānipāto"] = (
                                    vagga_jataka_counter["mahānipāto"] + 1
                                )
                                sequential_num = vagga_jataka_counter["mahānipāto"]

                                # Generate sutta code (two-digit: 22.jātaka)
                                sutta_code = f"22. {jātaka_num}."

                                # Generate web code (kn-jat-22-{jātaka})
                                web_code = f"kn-jat-22-{jātaka_num}"

                                # Create record immediately for Mahānipāto
                                record = {
                                    "bjt_sutta_code": sutta_code,
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": current_nipāta,  # nipāta
                                    "bjt_vagga": "",  # No vagga for Mahānipāto
                                    "bjt_sutta": jātaka_name,
                                }

                                results.append(record)
                                processed_jātaka_names.add(jātaka_name)
                                continue

                    # Look for jātaka story headings ending in "jātakaṃ."
                    # But skip if it's a Mahānipāto jātaka (handled separately)
                    elif (
                        (level == 1 or level == 2)
                        and re.match(r"^\d+\.\s*\w+.*jātakaṃ", text)
                        and "mahānipāto" not in current_nipāta.lower()
                    ):
                        jātaka_name = clean_jātaka_name(text)

                        # Check if we've already processed this jātaka name to avoid duplicates
                        if jātaka_name not in processed_jātaka_names:
                            # Extract jātaka number from the heading
                            jātaka_match = re.match(r"^(\d+)\.", text)
                            if jātaka_match:
                                jātaka_num = int(jātaka_match.group(1))

                                # For nipātas 8+, there are no vaggas, so use nipāta-level counting
                                if nipāta_num >= 8:
                                    # Use nipāta-level counter
                                    nipāta_key = f"{nipāta_num}"
                                    if nipāta_key not in vagga_jataka_counter:
                                        vagga_jataka_counter[nipāta_key] = 0
                                    vagga_jataka_counter[nipāta_key] = (
                                        vagga_jataka_counter[nipāta_key] + 1
                                    )
                                    sequential_num = vagga_jataka_counter[nipāta_key]

                                    # Generate sutta code (two-digit: nipāta.jātaka)
                                    sutta_code = f"{nipāta_num}. {jātaka_num}."

                                    # Generate web code (two-digit: kn-jat-{nipāta}-{jātaka})
                                    web_code = f"kn-jat-{nipāta_num}-{sequential_num}"

                                    # Empty vagga field
                                    vagga_field = ""
                                else:
                                    # Earlier nipātas have vaggas
                                    vagga_key = f"{nipāta_num}-{vagga_num}"
                                    vagga_jataka_counter[vagga_key] = (
                                        vagga_jataka_counter.get(vagga_key, 0) + 1
                                    )
                                    sequential_num = vagga_jataka_counter[vagga_key]

                                    # Generate sutta code
                                    sutta_code = (
                                        f"{nipāta_num}. {vagga_num}. {jātaka_num}."
                                    )

                                    # Generate web code
                                    web_code = f"kn-jat-{nipāta_num}-{vagga_num}-{sequential_num}"

                                    # Use current vagga
                                    vagga_field = current_vagga

                                # Create record
                                record = {
                                    "bjt_sutta_code": sutta_code,
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": current_nipāta,  # nipāta
                                    "bjt_vagga": vagga_field,
                                    "bjt_sutta": jātaka_name,
                                }

                                results.append(record)
                                processed_jātaka_names.add(jātaka_name)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {json_file}: {e}")
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

    return results


def save_to_tsv(data: List[Dict[str, Any]], output_file: Path):
    """Save data to TSV file."""
    if not data:
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

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(data)


def find_jat_files(json_dir: Path) -> List[Path]:
    """Find all kn-jat*.json files and sort them properly."""
    all_files = list(json_dir.glob("kn-jat*.json"))

    # Filter out atta-kn-jat files (commentaries)
    main_files = [f for f in all_files if not f.name.startswith("atta-")]

    # Custom sort function for proper ordering
    def sort_key(file):
        name = file.name
        if name == "kn-jat.json":
            return 0  # Main file first
        elif name == "kn-jat-5.json":
            return 5
        elif name == "kn-jat-11.json":
            return 11
        elif name == "kn-jat-15.json":
            return 15
        elif name == "kn-jat-18.json":
            return 18
        elif name == "kn-jat-22.json":
            return 22
        elif name == "kn-jat-22-6.json":
            return 22.6
        elif name == "kn-jat-22-10.json":
            return 22.10
        else:
            # Extract numeric part for any other files
            num = name.replace("kn-jat-", "").replace(".json", "")
            try:
                return float(num)
            except:
                return 999

    main_files.sort(key=sort_key)
    return main_files


def main():
    # Define paths
    json_dir = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/resources/dpd_submodules/bjt/public/static/roman_json"
    )
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn13_jat.tsv"
    )

    # Find all jātaka JSON files and sort them properly
    jat_files = find_jat_files(json_dir)

    if not jat_files:
        print("No jat JSON files found")
        return

    all_results = []

    for json_file in jat_files:
        print(f"Processing {json_file.name}...")

        # Extract jātaka data
        data = extract_jātaka_data(json_file)

        all_results.extend(data)
        print(f"Extracted {len(data)} jātakas from {json_file.name}")

    print(f"Total extracted: {len(all_results)} jātakas")

    # Save to TSV
    print(f"Saving to {output_file}...")
    save_to_tsv(all_results, output_file)
    print("Done!")


if __name__ == "__main__":
    main()
