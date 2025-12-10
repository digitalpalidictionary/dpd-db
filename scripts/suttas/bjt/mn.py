#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'mn-' and save to TSV.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
import sys

sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
from tools.sort_naturally import natural_sort


def clean_sutta_name(text: str) -> str:
    """Clean sutta name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def find_mn_files(json_dir: Path) -> List[Path]:
    """Find all JSON files starting with 'mn-' in directory."""
    mn_files = list(json_dir.glob("mn-*.json"))
    return natural_sort(mn_files)


def extract_sutta_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract sutta data from a single JSON file."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")

        # Get book ID from filename pattern (based on existing mn.tsv)
        book_id = 13  # Default for MN books
        if "mn-1" in filename or "mn-2" in filename:
            book_id = 13
        elif "mn-3" in filename:
            book_id = 14

        # Get pages
        pages = data.get("pages", [])

        current_piṭaka = "suttantapiṭake"
        current_nikaya = "majjhimanikāyo"
        current_book = ""
        current_vagga = ""

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
                    elif "majjhimanikāyo" in text.lower():
                        current_nikaya = text

                elif entry_type == "heading":
                    if "majjhimanikāyo" in text.lower():
                        current_nikaya = text
                    # Look for book/vagga headings like "mūlapaṇṇāsako", "mūlapariyāyavaggo"
                    elif "vaggo" in text.lower() and level <= 3:
                        current_vagga = clean_sutta_name(text)  # Apply cleaning to vagga names
                    elif "paṇṇāsako" in text.lower() and level <= 2:
                        current_book = clean_sutta_name(text)  # Apply cleaning to book names
                    # Look for sutta patterns in level 1 entries
                    elif level == 1:
                        # Look for sutta codes like "mn-1-1-1", "mn-2-1-3", etc.
                        sutta_match = re.search(r"mn-(\d+)-(\d+)-(\d+)", filename + " " + text)
                        if not sutta_match:
                            # Try to extract from filename only
                            sutta_match = re.search(r"mn-(\d+)-(\d+)-(\d+)", filename)
                        
                        if sutta_match:
                            book_num = int(sutta_match.group(1))
                            vagga_num = int(sutta_match.group(2))
                            sutta_num = int(sutta_match.group(3))
                            
                            # Use this entry if it looks like a sutta title
                            if not re.match(r"^\d+\.?\s*$", text) and len(text) > 0:
                                # Generate sutta code as "{book_num}-{vagga_num}-{sutta_num}"
                                sutta_code = f"{book_num}-{vagga_num}-{sutta_num}"
                                web_code = f"mn-{book_num}-{vagga_num}-{sutta_num}"
                                
                                # Clean the sutta name
                                cleaned_sutta_name = clean_sutta_name(text)
                                
                                # Create record with the required 13 fields
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
                                    "bjt_minor_section": "",  # MN doesn't use paṇṇāsa as minor section in this context
                                    "bjt_vagga": current_vagga,  # Apply cleaning if needed
                                    "bjt_sutta": cleaned_sutta_name,
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
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/mn.tsv"
    )

    # Check if JSON directory exists
    if not json_dir.exists():
        print(f"JSON directory not found: {json_dir}")
        return

    # Find all mn- files
    mn_files = find_mn_files(json_dir)
    print(f"Found {len(mn_files)} mn- JSON files")

    if not mn_files:
        print("No mn- JSON files found")
        return

    all_data = []
    for json_file in mn_files:
        print(f"Processing {json_file.name}...")
        data = extract_sutta_data(json_file)
        all_data.extend(data)
        print(f"  Extracted {len(data)} records")

    # Save to TSV
    print(f"\nTotal records extracted: {len(all_data)}")
    print(f"Saving to {output_file}...")
    save_to_tsv(all_data, output_file)
    print("Done!")


if __name__ == "__main__":
    main()