#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON files kn-snp*.json and save to TSV.
SNP has Vagga -> Sutta structure.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re
import sys
sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
from tools.sort_naturally import natural_sort


def sort_snp_files(file_list):
    """Custom sort for kn-snp files to handle kn-snp.json (no number) coming first."""
    def sort_key(filename):
        name = filename.name
        if name == "kn-snp.json":
            return (0, 1)  # First file
        elif name.startswith("kn-snp-"):
            # Extract number after kn-snp-
            num_part = name.replace("kn-snp-", "").replace(".json", "")
            try:
                num = int(num_part)
                return (0, num + 1)  # kn-snp-1.json should be second, etc.
            except ValueError:
                return (1, name)
        else:
            return (2, name)
    
    return sorted(file_list, key=sort_key)


def clean_sutta_name(text: str) -> str:
    """Clean sutta name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def extract_sutta_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract sutta data from kn-snp*.json files."""
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
        current_book = "suttanipātapāḷi"
        current_vagga = ""
        sutta_counter = 0
        last_web_sutta_num = 0
        current_vagga_for_web = ""
        
        # Reset counters for each file to ensure proper sequencing
        last_web_sutta_num = 0
        current_vagga_for_web = ""

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
                    if "khuddakanikāye" in text.lower():
                        current_piṭaka = text
                    # Look for sutta numbers like "1. 1.", "2. 1.", "4-13.", etc.
                    elif re.match(r"^\d+[\.\-]\s*\d+\.$", text):
                        sutta_counter += 1

                        # Extract sutta numbers
                        sutta_match = re.match(r"^(\d+)\.\s*(\d+)\.$", text)
                        if sutta_match:
                            vagga_num = int(sutta_match.group(1))
                            sutta_num = int(sutta_match.group(2))

                            # Check if vagga changed and reset web counter if needed
                            if current_vagga != current_vagga_for_web:
                                last_web_sutta_num = 0
                                current_vagga_for_web = current_vagga

                            # Always increment by 1 from previous sutta
                            web_sutta_num = last_web_sutta_num + 1

                            # Generate sutta_code as "{vagga_num}. {sutta_num}."
                            sutta_code = f"{vagga_num}. {sutta_num}."

                            # Generate web_code as "kn-snp-{vagga_num}-{web_sutta_num}"
                            web_code = f"kn-snp-{vagga_num}-{web_sutta_num}"
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
                                    if not re.match(r"^\d+\.\s*\d+\.$", next_text):
                                        # Clean up sutta name
                                        sutta_name = clean_sutta_name(next_text)

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
                                "bjt_minor_section": "",  # Empty for SNP (doesn't have nipāta structure)
                                "bjt_vagga": current_vagga,
                                "bjt_sutta": sutta_name,
                            }

                            results.append(record)

                elif entry_type == "heading":
                    if "suttanipāto" in text.lower():
                        current_book = text
                    # Special case: vatthugāthā in 5th vagga should be treated as 5. 0.
                    elif text == "vatthugāthā" and level == 1 and "pārāyanavaggo" in current_vagga:
                        # Create record for vatthugāthā as 5. 0.
                        sutta_code = "5. 0."
                        web_code = "kn-snp-5-0"  # Use actual sutta number from sutta_code
                        
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
                            "bjt_minor_section": "",  # Empty for SNP
                            "bjt_vagga": current_vagga,
                            "bjt_sutta": text,
                        }
                        results.append(record)
                    
                    # Special case: pārāyanatthutigāthā in 5th vagga - should be 5. 17.
                    elif "atthutigāthā" in text.lower() and level == 1 and "pārāyanavaggo" in current_vagga:
                        # This should be the 17th sutta in the pārāyanavaggo (after 0-16)
                        sutta_num = 17
                        sutta_code = f"5. {sutta_num}."
                        web_code = f"kn-snp-5-{sutta_num}"
                        
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
                            "bjt_minor_section": "",  # Empty for SNP
                            "bjt_vagga": current_vagga,
                            "bjt_sutta": text,
                        }
                        results.append(record)
                    
                    # Special case: pārāyanānugītigāthā in 5th vagga - should follow the sequence after other suttas in the vagga
                    elif text == "pārāyanānugītigāthā" and level == 1 and "pārāyanavaggo" in current_vagga:
                        # Count existing suttas in this vagga to determine the next number
                        existing_suttas_in_vagga = [r for r in results if r["bjt_vagga"] == current_vagga and r["bjt_sutta_code"].startswith("5.")]
                        sutta_num = len(existing_suttas_in_vagga) + 1
                        
                        # Create record with calculated sutta number
                        sutta_code = f"5. {sutta_num}."
                        web_code = f"kn-snp-5-{sutta_num}"
                        
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
                            "bjt_minor_section": "",  # Empty for SNP
                            "bjt_vagga": current_vagga,
                            "bjt_sutta": text,
                        }
                        results.append(record)
                    
                    # Look for vagga headings like "1. uragavaggo", "2. cullavaggo", etc.
                    elif re.match(r"^\d+\.\s*\w+.*vaggo?$", text) and level == 3:
                        current_vagga = text
                        sutta_counter = 0  # Reset sutta counter for new vagga
                        last_web_sutta_num = 0
                        current_vagga_for_web = current_vagga

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
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn5_snp.tsv"
    )

    # Find all kn-snp*.json files
    snp_files = sort_snp_files(list(json_dir.glob("kn-snp*.json")))
    
    if not snp_files:
        print("No kn-snp*.json files found")
        return

    print(f"Found {len(snp_files)} files to process:")
    for f in snp_files:
        print(f"  - {f.name}")

    all_data = []

    # Process each file
    for json_file in snp_files:
        print(f"Processing {json_file.name}...")
        data = extract_sutta_data(json_file)
        all_data.extend(data)
        print(f"  Extracted {len(data)} suttas")

    print(f"Total extracted: {len(all_data)} suttas")

    # Save to TSV
    print(f"Saving to {output_file}...")
    save_to_tsv(all_data, output_file)
    print("Done!")


if __name__ == "__main__":
    main()