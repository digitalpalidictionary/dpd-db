#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'an-' and save to TSV.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
import sys

sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
from tools.sort_naturally import natural_sort_hyphenated


def clean_sutta_name(text: str) -> str:
    """Clean sutta name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def find_an_files(json_dir: Path) -> List[Path]:
    """Find all JSON files starting with 'an-' in directory."""
    an_files = list(json_dir.glob("an-*.json"))
    return natural_sort_hyphenated(an_files)


def get_book_number(filename: str) -> str:
    """Extract base book number from filename like 'an-1', 'an-2', 'an-3-1'"""
    # Remove 'an-' prefix and take the first number before any additional '-'
    return filename.replace('an-', '').split('-')[0]


def extract_sutta_data(
    json_file: Path,
    current_piṭaka: str,
    current_nikaya: str,
    current_book: str,
    current_paṇṇāsa: str,
    current_vagga: str,
    last_web_sutta_num: int,
    current_vagga_for_web: str,
) -> tuple[List[Dict[str, Any]], int, str]:
    """Extract sutta data from a single JSON file."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")

        # Get book ID from filename (e.g., "an-1" -> "22")
        # Based on bak file, an-1 = 22, an-2 = 22, etc.
        book_id_map = {
            "an-1": 22,
            "an-2": 22,
            "an-3": 22,
            "an-4": 23,
            "an-5": 24,
            "an-6": 25,
            "an-7": 25,
            "an-8": 26,
            "an-9": 26,
            "an-10": 27,
            "an-11": 27,
        }
        book_id = book_id_map.get(filename, 22)  # Default to 22

        # Get pages
        pages = data.get("pages", [])

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
                    elif "aṅguttaranikāyo" in text.lower():
                        current_nikaya = text
                    elif "nipāto" in text.lower():
                        current_book = clean_sutta_name(text)
                    elif "paṇṇāsako" in text.lower() and level == 3:
                        current_paṇṇāsa = text
                    elif level == 1 and re.match(r"^\d+\.\s*\d+\.\s*\d+", text):
                        # This is a sutta code like "1. 1. 1." in centered entries (an-4 pattern)
                        # Parse the sutta code
                        sutta_parts = text.rstrip(".").split(".")
                        if len(sutta_parts) >= 3:
                            try:
                                nipata_num = int(sutta_parts[0].strip())
                                vagga_num = int(sutta_parts[1].strip())
                                sutta_part = sutta_parts[2].strip()

                                # Check if vagga changed and reset web counter if needed
                                if current_vagga != current_vagga_for_web:
                                    last_web_sutta_num = 0
                                    current_vagga_for_web = current_vagga
                                
                                # Always increment by 1 from previous sutta
                                web_sutta_num = last_web_sutta_num + 1
                                # Keep original format for bjt_sutta_code
                                sutta_code = text.rstrip(".")
                                web_code = f"an-{nipata_num}-{vagga_num}-{web_sutta_num}"
                                last_web_sutta_num = web_sutta_num

                                # Look ahead for sutta name in next entry
                                sutta_name = text  # fallback to number
                                entry_index = pali_entries.index(entry)
                                if entry_index + 1 < len(pali_entries):
                                    next_entry = pali_entries[entry_index + 1]
                                    if (
                                        next_entry.get("type") == "heading"
                                        and next_entry.get("level") == 1
                                    ):
                                        next_text = next_entry.get("text", "").strip()
                                        # Check if it's a sutta name (not another number)
                                        if not re.match(
                                            r"^\d+\.\s*\d+\.\s*\d+", next_text
                                        ):
                                            # Clean up sutta name: remove brackets, vaggo, and curly braces
                                            sutta_name = next_text
                                            sutta_name = sutta_name.replace(
                                                "[", ""
                                            ).replace("]", "")  # Remove brackets
                                            sutta_name = re.sub(
                                                r"\{[^}]*\}", "", sutta_name
                                            )  # Remove {.*} patterns

                                # Create record
                                record = {
                                    "bjt_sutta_code": sutta_code,
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,  # Always 0 based on backup
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": current_paṇṇāsa,  # Renamed from bjt_paṇṇāsa
                                    "bjt_vagga": current_vagga,
                                    "bjt_sutta": sutta_name,
                                }

                                results.append(record)

                            except (ValueError, IndexError):
                                # Skip invalid sutta codes
                                pass

                elif entry_type == "heading":
                    if "nipāto" in text.lower():
                        current_book = clean_sutta_name(text)
                    elif "paṇṇāsako" in text.lower() and level == 3:
                        current_paṇṇāsa = text
                    elif "vaggo" in text.lower() and level <= 3:
                        current_vagga = clean_sutta_name(text)  # Clean brackets and footnotes
                    elif level == 1 and re.match(r"^\d+\.\s*\d+\.\s*\d+", text):
                        # This is a sutta code like "1. 1. 1." in heading entries (an-1 pattern)
                        # Parse the sutta code
                        sutta_parts = text.rstrip(".").split(".")
                        if len(sutta_parts) >= 3:
                            try:
                                nipata_num = int(sutta_parts[0].strip())
                                vagga_num = int(sutta_parts[1].strip())
                                sutta_part = sutta_parts[2].strip()

                                # Check if vagga changed and reset web counter if needed
                                if current_vagga != current_vagga_for_web:
                                    last_web_sutta_num = 0
                                    current_vagga_for_web = current_vagga
                                
                                # Always increment by 1 from previous sutta
                                web_sutta_num = last_web_sutta_num + 1
                                # Keep original format for bjt_sutta_code
                                sutta_code = text.rstrip(".")
                                web_code = f"an-{nipata_num}-{vagga_num}-{web_sutta_num}"
                                last_web_sutta_num = web_sutta_num

                                # Look ahead for sutta name in next entry
                                sutta_name = text  # fallback to number
                                entry_index = pali_entries.index(entry)
                                if entry_index + 1 < len(pali_entries):
                                    next_entry = pali_entries[entry_index + 1]
                                    if (
                                        next_entry.get("type") == "heading"
                                        and next_entry.get("level") == 1
                                    ):
                                        next_text = next_entry.get("text", "").strip()
                                        # Check if it's a sutta name (not another number)
                                        if not re.match(
                                            r"^\d+\.\s*\d+\.\s*\d+", next_text
                                        ):
                                            # Clean up sutta name: remove brackets, vaggo, and curly braces
                                            sutta_name = next_text
                                            sutta_name = sutta_name.replace(
                                                "[", ""
                                            ).replace("]", "")  # Remove brackets
                                            sutta_name = re.sub(
                                                r"\{[^}]*\}", "", sutta_name
                                            )  # Remove {.*} patterns
                                            sutta_name = sutta_name.replace(
                                                "vaggo", ""
                                            ).strip()  # Remove vaggo

                                # Create record
                                record = {
                                    "bjt_sutta_code": sutta_code,
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,  # Always 0 based on backup
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": "",  # Mostly blank
                                    "bjt_book": current_book,
                                    "bjt_minor_section": current_paṇṇāsa,  # Renamed from bjt_paṇṇāsa
                                    "bjt_vagga": current_vagga,
                                    "bjt_sutta": sutta_name,
                                }

                                results.append(record)

                            except (ValueError, IndexError):
                                # Skip invalid sutta codes
                                pass

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in {json_file}: {e}")
    except Exception as e:
        print(f"Error processing {json_file}: {e}")

    return results, last_web_sutta_num, current_vagga_for_web


def save_to_tsv(data: List[Dict[str, Any]], output_file: Path):
    """Save data to TSV file."""
    if not data:
        print("No data to save")
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
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/an.tsv"
    )

    # Check if JSON directory exists
    if not json_dir.exists():
        print(f"JSON directory not found: {json_dir}")
        return

    # Find all an- files
    an_files = find_an_files(json_dir)
    print(f"Found {len(an_files)} an- JSON files")

    if not an_files:
        print("No an- JSON files found")
        return

    # Global hierarchy state to preserve across files
    current_piṭaka = "suttantapiṭake"
    current_nikaya = "aṅguttaranikāyo"
    current_book = ""
    current_paṇṇāsa = ""
    current_vagga = ""
    last_web_sutta_num = 0
    current_vagga_for_web = ""

# Process each file
    all_data = []
    for json_file in an_files:
        print(f"Processing {json_file.name}...")
        
        # Reset hierarchy when moving to a new book (not just new file)
        filename = json_file.stem
        if all_data:  # Not the first file
            last_record = all_data[-1]
            last_filename = last_record["bjt_filename"]
            
            # Get current and previous book numbers
            current_book_num = get_book_number(filename)
            last_book_num = get_book_number(last_filename)
            
            # Only reset if moving to a different book
            if current_book_num != last_book_num:
                current_piṭaka = "suttantapiṭake"
                current_nikaya = "aṅguttaranikāyo" 
                current_book = ""
                current_paṇṇāsa = ""
                current_vagga = ""
        
        data, last_web_sutta_num, current_vagga_for_web = extract_sutta_data(json_file, current_piṭaka, current_nikaya, current_book, current_paṇṇāsa, current_vagga, last_web_sutta_num, current_vagga_for_web)
        
        # Update hierarchy state for next record within same file
        if data:
            last_record = data[-1]  # Get the last record to extract current hierarchy
            current_piṭaka = last_record["bjt_piṭaka"]
            current_nikaya = last_record["bjt_nikāya"]
            current_book = last_record["bjt_book"]
            current_paṇṇāsa = last_record["bjt_minor_section"]
            current_vagga = last_record["bjt_vagga"]
        
        all_data.extend(data)
        print(f"  Extracted {len(data)} records")

    # Save to TSV
    print(f"\nTotal records extracted: {len(all_data)}")
    print(f"Saving to {output_file}...")
    save_to_tsv(all_data, output_file)
    print("Done!")


if __name__ == "__main__":
    main()
