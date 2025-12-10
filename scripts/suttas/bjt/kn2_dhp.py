#!/usr/bin/env python3
"""
Script to extract vagga data from BJT JSON file kn-dhp.json and save to TSV.
DHP has vaggas but no individual suttas - vaggas are the main entries.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
import sys

# sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
# from tools.sort_naturally import natural_sort


def clean_vagga_name(text: str) -> str:
    """Clean vagga name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def extract_vagga_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract vagga data from kn-dhp.json file."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")
        book_id = 28  # KN books use book_id 28

        # Get pages
        pages = data.get("pages", [])
        
        current_piṭaka = "suttantapiṭake"
        current_nikaya = "khuddakanikāyo"
        current_book = "dhammapadapāḷi"
        vagga_counter = 0

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
                    elif "khuddakanikāyo" in text.lower():
                        current_nikaya = text

                elif entry_type == "heading":
                    if "dhammapadapāḷi" in text.lower():
                        current_book = text
                    # Look for vagga headings like "1. yamakavaggo" or "14. buddhavaggo."
                    elif re.match(r"^\d+\.\s+.+vaggo\.?$", text):
                        vagga_counter += 1
                        
                        # Extract vagga number and name
                        vagga_match = re.match(r"^(\d+)\.\s+(.+)$", text)
                        if vagga_match:
                            vagga_num = int(vagga_match.group(1))
                            vagga_name = vagga_match.group(2).strip().rstrip(".")
                            
                            # Generate sutta_code as "{vagga_num}."
                            sutta_code = f"{vagga_num}."
                            
                            # Generate web_code as "kn-dhp-{vagga_num}"
                            web_code = f"kn-dhp-{vagga_num}"
                            
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
                                "bjt_minor_section": "",  # Empty for DHP
                                "bjt_vagga": vagga_name,
                                "bjt_sutta": "",  # Empty - no individual suttas in DHP
                            }

                            results.append(record)

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
    json_file = json_dir / "kn-dhp.json"
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn2_dhp.tsv"
    )

    # Check if JSON file exists
    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        return

    print(f"Processing {json_file.name}...")
    
    # Extract vagga data
    data = extract_vagga_data(json_file)
    
    print(f"Extracted {len(data)} vaggas")

    # Save to TSV
    print(f"Saving to {output_file}...")
    save_to_tsv(data, output_file)
    print("Done!")


if __name__ == "__main__":
    main()