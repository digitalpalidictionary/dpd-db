#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files starting with 'sn-' and save to TSV.
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


def find_sn_files(json_dir: Path) -> List[Path]:
    """Find all JSON files starting with 'sn-' in directory."""
    sn_files = list(json_dir.glob("sn-*.json"))
    return natural_sort(sn_files)


def extract_sutta_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract sutta data from a single JSON file."""
    results = []

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        filename = data.get("filename", "")

        # Get book ID from filename pattern (based on existing sn.tsv)
        book_id = 16  # Default for SN books
        if "sn-1" in filename or "sn-2" in filename:
            book_id = 16
        elif "sn-3" in filename:
            book_id = 17
        elif "sn-4" in filename or "sn-5" in filename:
            book_id = 18

        # Get pages
        pages = data.get("pages", [])

        current_piṭaka = "suttantapiṭake"
        current_nikaya = "saṃyuttanikāyo"
        current_mahāvagga = ""
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
                    elif "saṃyuttanikāyo" in text.lower():
                        current_nikaya = text

                elif entry_type == "heading":
                    if "saṃyuttanikāyo" in text.lower():
                        current_nikaya = text
                    # Look for mahāvagga headings like "sagāthavaggo", "nidanavaggo"
                    elif "vaggo" in text.lower() and level == 2:
                        current_mahāvagga = clean_sutta_name(text)  # Apply cleaning
                    # Look for book/saṃyutta headings like "devatāsaṃyuttaṃ", "sattasaṃyuttaṃ"
                    elif "saṃyutta" in text.lower() and level == 3:
                        current_book = clean_sutta_name(text)  # Apply cleaning
                    # Look for vagga headings like "saggo", "nandana vaggo"
                    elif "vaggo" in text.lower() and level == 4:
                        current_vagga = clean_sutta_name(text)  # Apply cleaning
                    # Look for sutta patterns in level 1 entries
                    elif level == 1:
                        # Look for sutta codes like "sn-1-1-1-1", "sn-2-3-4-5", etc.
                        # Extract from the text that looks like a sutta number
                        sutta_pattern = r"sn-(\d+)-(\d+)-(\d+)-(\d+)"
                        filename_match = re.search(sutta_pattern, filename)
                        text_match = re.search(r"sn-(\d+)-(\d+)-(\d+)-(\d+)", text)
                        
                        if filename_match or text_match:
                            match = filename_match or text_match
                            mahavagga_num = int(match.group(1))
                            book_num = int(match.group(2))
                            vagga_num = int(match.group(3))
                            sutta_num = int(match.group(4))
                            
                            # Use this entry if it looks like a sutta title
                            if not re.match(r"^\d+\.?\s*$", text) and len(text) > 0:
                                # Generate sutta code as "{mahavagga_num}. {book_num}. {vagga_num}. {sutta_num}."
                                sutta_code = f"{mahavagga_num}. {book_num}. {vagga_num}. {sutta_num}."
                                web_code = f"sn-{mahavagga_num}-{book_num}-{vagga_num}-{sutta_num}"
                                
                                # Clean the sutta name
                                cleaned_sutta_name = clean_sutta_name(text)
                                
                                # Create record with the required 13 fields
                                record = {
                                    "bjt_sutta_code": sutta_code.rstrip("."),
                                    "bjt_web_code": web_code,
                                    "bjt_filename": filename,
                                    "bjt_book_id": book_id,
                                    "bjt_page_num": page_num,
                                    "bjt_page_offset": 0,
                                    "bjt_piṭaka": current_piṭaka,
                                    "bjt_nikāya": current_nikaya,
                                    "bjt_major_section": current_mahāvagga,  # Use mahāvagga as major section
                                    "bjt_book": current_book,
                                    "bjt_minor_section": "",  # SN doesn't use minor section the same way as AN
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
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/sn.tsv"
    )

    # Check if JSON directory exists
    if not json_dir.exists():
        print(f"JSON directory not found: {json_dir}")
        return

    # Find all sn- files
    sn_files = find_sn_files(json_dir)
    print(f"Found {len(sn_files)} sn- JSON files")

    if not sn_files:
        print("No sn- JSON files found")
        return

    all_data = []
    for json_file in sn_files:
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