#!/usr/bin/env python3
"""
Script to extract gāthā data from BJT JSON file kn-thig.json and save to TSV.
Therīgāthā has Nipāta -> Vagga -> Gāthā structure (nipātas 1-2) and Nipāta -> Gāthā structure (nipātas 3+).
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re


# Global sequential counter for web codes across all nipātas
global_web_sutta_counter = 0

# Global tracking of encountered nipata sequence
global_encountered_nipata_sequence = {}
global_next_nipata_seq_num = 1


def clean_gāthā_name(text: str) -> str:
    """Clean gāthā name by removing brackets, curly braces, and trailing fullstops."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    cleaned = cleaned.rstrip(".")  # Remove trailing fullstops
    return cleaned.strip()


def extract_gāthā_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract gāthā data from kn-thig.json file."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")
        book_id = 28  # KN books use book_id 28

        # Get pages
        pages = data.get("pages", [])

        # Access the global counters
        global global_web_sutta_counter
        global global_encountered_nipata_sequence
        global global_next_nipata_seq_num

        current_piṭaka = "suttantapiṭake"
        current_nikaya = "khuddakanikāyo"
        current_book = "therīgāthāpāḷi"
        current_nipāta = ""
        current_vagga = ""

        nipāta_num = 0
        vagga_num = 0

        # Track sutta numbers within each section
        nipāta_sutta_counter = {}
        vagga_sutta_counter = {}

        # Track processed sutta numbers to avoid duplicates
        processed_sutta_numbers = set()

        # Track pending sutta numbers waiting for names
        pending_suttas = {}

        # Flag to detect Sumedhātherīgāthā special case
        found_sumedha = False

        # Track processed sutta names to avoid duplicates
        processed_sutta_names = set()

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
                        current_piṭaka = text
                    elif level == 1:
                        # Look for sutta numbers - all nipātas use "nipāta.vagga.sutta" format
                        if re.match(r"^\d+\.\s*\d+\.\s*\d+\.", text):
                            # Skip if we've already processed this exact sutta number (avoid Pali/Sinhala duplicates)
                            if text in processed_sutta_numbers:
                                continue

                            # Mark as processed to avoid duplicates
                            processed_sutta_numbers.add(text)

                            # Parse sutta code and store as pending
                            sutta_parts = text.rstrip(".").split(".")
                            if len(sutta_parts) >= 3:
                                try:
                                    parsed_nipāta = int(sutta_parts[0].strip())
                                    parsed_vagga = int(sutta_parts[1].strip())
                                    parsed_sutta = int(sutta_parts[2].strip())

                                    # Store sutta info as pending, waiting for name
                                    pending_suttas[text] = {
                                        "parsed_nipāta": parsed_nipāta,
                                        "parsed_vagga": parsed_vagga,
                                        "parsed_sutta": parsed_sutta,
                                        "page_num": page_num,
                                    }

                                except (ValueError, IndexError):
                                    continue
                        else:
                            # Nipātas 3+: pattern "3. 1." (nipāta.sutta)
                            if re.match(r"^\d+\.\s*\d+\.", text):
                                # Parse the sutta code
                                sutta_parts = text.rstrip(".").split(".")
                                if len(sutta_parts) >= 2:
                                    try:
                                        parsed_nipāta = int(sutta_parts[0].strip())
                                        parsed_sutta = int(sutta_parts[1].strip())

                                        # Store sutta info as pending, waiting for name
                                        pending_suttas[text] = {
                                            "parsed_nipāta": parsed_nipāta,
                                            "parsed_vagga": 0,  # No vagga for nipātas 3+
                                            "parsed_sutta": parsed_sutta,
                                            "page_num": page_num,
                                        }

                                    except (ValueError, IndexError):
                                        continue

                elif entry_type == "heading":
                    if "therīgāthāpāḷi" in text.lower():
                        current_book = text

                    # Check if this is a sutta name heading
                    elif (
                        level == 1 and "therīgāthā" in text and text != "therīgāthāpāḷi"
                    ):
                        # This is a sutta name heading - find matching pending sutta
                        sutta_name = clean_gāthā_name(text)

                        # Special case: Sumedhātherīgāthā
                        if "sumedhātherīgāthā" in text.lower():
                            # Check if we've already processed sumedhātherīgāthā to avoid duplicates
                            if "sumedhātherīgāthā" not in processed_sutta_names:
                                found_sumedha = True
                                # Create special record for Sumedhātherīgāthā
                                record = {
                                    "bjt_sutta_code": "kn-thig-1-2",  # Second entry in mahānipāto
                                    "bjt_web_code": "kn-thig-16-1",  # Maps to web nipāta 16, sutta 1
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": "mahānipāto",  # Special section
                                    "bjt_vagga": "",
                                    "bjt_sutta": sutta_name,
                                }
                                results.append(record)
                                processed_sutta_names.add("sumedhātherīgāthā")
                            continue

                        # Find the most recent pending sutta (before this heading)
                        if pending_suttas:
                            # Get the last pending sutta (the one that comes just before this heading)
                            last_sutta_code = max(
                                pending_suttas.keys(),
                                key=lambda x: (
                                    pending_suttas[x]["parsed_nipāta"],
                                    pending_suttas[x]["parsed_vagga"]
                                    if "parsed_vagga" in pending_suttas[x]
                                    else 0,
                                    pending_suttas[x]["parsed_sutta"],
                                ),
                            )

                            sutta_info = pending_suttas[last_sutta_code]

                            # Generate web code based on nipāta number
                            # For KN 9: irregular nipātas > 9 map to sequential web nipātas starting from 10
                            actual_nipata = sutta_info["parsed_nipāta"]
                            if actual_nipata <= 9:
                                web_nipata_num = actual_nipata
                            elif actual_nipata == 11:
                                web_nipata_num = 10
                            elif actual_nipata == 12:
                                web_nipata_num = 11
                            elif actual_nipata == 16:
                                web_nipata_num = 12
                            elif actual_nipata == 20:
                                web_nipata_num = 13
                            elif actual_nipata == 30:
                                web_nipata_num = 14
                            elif actual_nipata == 40:
                                web_nipata_num = 15
                            else:
                                web_nipata_num = actual_nipata  # fallback

                            # Use the actual sutta number from the sutta code
                            actual_sutta_number = sutta_info["parsed_sutta"]

                            # Generate web code as kn-thig-{web_nipata}-{actual_sutta}
                            web_code = f"kn-thig-{web_nipata_num}-{actual_sutta_number}"

                            if sutta_info["parsed_nipāta"] <= 2:
                                # Nipātas 1-2: increment counter for this vagga
                                vagga_key = f"{sutta_info['parsed_nipāta']}-{sutta_info['parsed_vagga']}"
                                vagga_sutta_counter[vagga_key] = (
                                    vagga_sutta_counter.get(vagga_key, 0) + 1
                                )
                                sutta_num = vagga_sutta_counter[vagga_key]
                                vagga_field = current_vagga
                            else:
                                # Nipātas 3+: increment counter for this nipāta
                                nipāta_sutta_counter[sutta_info["parsed_nipāta"]] = (
                                    nipāta_sutta_counter.get(
                                        sutta_info["parsed_nipāta"], 0
                                    )
                                    + 1
                                )
                                sutta_num = nipāta_sutta_counter[
                                    sutta_info["parsed_nipāta"]
                                ]
                                vagga_field = ""  # No vaggas in nipātas 3+

                            # Check if we've already processed this sutta name to avoid duplicates
                            if sutta_name not in processed_sutta_names:
                                # Create record
                                record = {
                                    "bjt_sutta_code": last_sutta_code,
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": sutta_info["page_num"],
                                    "bjt_page_offset": 0,
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": current_nipāta,  # Renamed from bjt_nipāta
                                    "bjt_vagga": vagga_field,
                                    "bjt_sutta": sutta_name,
                                }

                                results.append(record)
                                processed_sutta_names.add(sutta_name)

                            # Remove this sutta from pending
                            del pending_suttas[last_sutta_code]

                    # Look for nipāta headings like "1. ekakanipāto.", "2. dutiyapāto.", etc.
                    elif level == 3 and re.match(r"^\d+\.\s*\w+.*nipāto", text):
                        # Remove trailing fullstop from nipāta heading
                        current_nipāta = re.sub(r"\.$", "", text)
                        nipāta_match = re.match(r"^(\d+)", text)
                        if nipāta_match:
                            nipāta_num = int(nipāta_match.group(1))
                            # Reset counters for new nipāta
                            if nipāta_num not in nipāta_sutta_counter:
                                nipāta_sutta_counter[nipāta_num] = 0
                        current_vagga = ""
                        vagga_num = 0

                    # Look for vagga headings (only in nipātas 1-2)
                    elif (
                        level == 2
                        and nipāta_num <= 2
                        and re.match(r"^\d+\.\s*\w+.*vaggo", text)
                    ):
                        current_vagga = text
                        vagga_match = re.match(r"^(\d+)", text)
                        if vagga_match:
                            vagga_num = int(vagga_match.group(1))
                            # Initialize counter for this vagga
                            vagga_key = f"{nipāta_num}-{vagga_num}"
                            if vagga_key not in vagga_sutta_counter:
                                vagga_sutta_counter[vagga_key] = 0

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


def main():
    # Define paths
    json_dir = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/resources/dpd_submodules/bjt/public/static/roman_json"
    )
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn9_thig.tsv"
    )

    # Only process kn-thig.json (exclude atta-kn-thig.json)
    thig_files = [json_dir / "kn-thig.json"]

    # Reset global counters at start
    global global_web_sutta_counter
    global global_encountered_nipata_sequence
    global global_next_nipata_seq_num
    global_web_sutta_counter = 0
    global_encountered_nipata_sequence = {}
    global_next_nipata_seq_num = 1

    if not thig_files:
        print("No thig JSON files found")
        return

    all_results = []

    for json_file in thig_files:
        print(f"Processing {json_file.name}...")

        # Extract gāthā data
        data = extract_gāthā_data(json_file)

        all_results.extend(data)
        print(f"Extracted {len(data)} gāthās from {json_file.name}")

    print(f"Total extracted: {len(all_results)} gāthās")

    # Save to TSV
    print(f"Saving to {output_file}...")
    save_to_tsv(all_results, output_file)
    print("Done!")


if __name__ == "__main__":
    main()
