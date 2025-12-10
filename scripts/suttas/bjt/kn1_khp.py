#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON file kn-khp.json and save to TSV.
KHP has simple list of suttas with no vaggas.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
import sys

# sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
# from tools.sort_naturally import natural_sort


def clean_sutta_name(text: str) -> str:
    """Clean sutta name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def extract_sutta_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract sutta data from kn-khp.json file."""
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
        current_book = "khuddakapāṭhapāḷi"
        sutta_counter = 0

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
                    if "khuddakapāṭhapāḷi" in text.lower():
                        current_book = text
                    # Look for sutta headings like "1. saraṇagamanaṃ{1}"
                    elif re.match(r"^\d+\.\s+.+$", text):
                        sutta_counter += 1
                        
                        # Extract sutta number and name
                        sutta_match = re.match(r"^(\d+)\.\s+(.+)$", text)
                        if sutta_match:
                            sutta_num = int(sutta_match.group(1))
                            sutta_name = sutta_match.group(2).strip()
                            
                            # Clean sutta name (remove {1} etc.)
                            sutta_name = re.sub(r"\{[^}]*\}", "", sutta_name)
                            
                            # Generate sutta_code as "{sutta_num}."
                            sutta_code = f"{sutta_num}."
                            
                            # Generate web_code as "kn-khp-{sutta_num}"
                            web_code = f"kn-khp-{sutta_num}"
                            
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
                                "bjt_minor_section": "",  # Empty for KHP
                                "bjt_vagga": "",  # Empty for KHP - no vaggas
                                "bjt_sutta": sutta_name,
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
    json_file = json_dir / "kn-khp.json"
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn1_khp.tsv"
    )

    # Check if JSON file exists
    if not json_file.exists():
        print(f"JSON file not found: {json_file}")
        return

    print(f"Processing {json_file.name}...")
    
    # Extract sutta data
    data = extract_sutta_data(json_file)
    
    print(f"Extracted {len(data)} suttas")

    # Save to TSV
    print(f"Saving to {output_file}...")
    save_to_tsv(data, output_file)
    print("Done!")


if __name__ == "__main__":
    main()