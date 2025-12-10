#!/usr/bin/env python3
"""
Script to extract sutta data from BJT JSON file kn-iti.json and save to TSV.
ITI has Nipāta -> Vagga -> Sutta structure.
"""

import json
from pathlib import Path
import csv
from typing import List, Dict, Any
import re

# sys.path.append("/home/bodhirasa/MyFiles/3_Active/dpd-db/tools")
# from tools.sort_naturally import natural_sort


def clean_sutta_name(text: str) -> str:
    """Clean sutta name by removing brackets and curly braces only."""
    cleaned = text.replace("[", "").replace("]", "")  # Remove brackets
    cleaned = re.sub(r"\{[^}]*\}", "", cleaned)  # Remove {.*} patterns
    return cleaned.strip()


def extract_sutta_data(json_file: Path) -> List[Dict[str, Any]]:
    """Extract sutta data from kn-iti.json file."""
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
        current_book = "itivuttakapāḷi"
        current_nipāta = ""
        current_vagga = ""
        sutta_counter = 0
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
                    if "suttantapiṭake" in text.lower():
                        current_piṭaka = text
                    elif "khuddakanikāyo" in text.lower():
                        current_nikaya = text
                    # Look for sutta numbers like "1. 1. 1.", "1. 1. 2.", etc.
                    elif re.match(r"^\d+\.\s*\d+\.\s*\d+\.$", text):
                        sutta_counter += 1

                        # Extract sutta numbers
                        sutta_match = re.match(r"^(\d+)\.\s*(\d+)\.\s*(\d+)\.$", text)
                        if sutta_match:
                            nipāta_num = int(sutta_match.group(1))
                            vagga_num = int(sutta_match.group(2))
                            sutta_num = int(sutta_match.group(3))

                            # Check if vagga changed and reset web counter if needed
                            if current_vagga != current_vagga_for_web:
                                last_web_sutta_num = 0
                                current_vagga_for_web = current_vagga

                            # Always increment by 1 from previous sutta
                            web_sutta_num = last_web_sutta_num + 1

                            # Generate sutta_code as "{nipāta_num}. {vagga_num}. {sutta_num}."
                            sutta_code = f"{nipāta_num}. {vagga_num}. {sutta_num}."

                            # Special case for Catukkanipāto: omit vagga number in web_code
                            if "catukkanipāto" in current_nipāta.lower():
                                web_code = f"kn-iti-{nipāta_num}-{web_sutta_num}"
                            else:
                                web_code = f"kn-iti-{nipāta_num}-{vagga_num}-{web_sutta_num}"
                            
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
                                        r"^\d+\.\s*\d+\.\s*\d+\.$", next_text
                                    ):
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
                                "bjt_minor_section": current_nipāta,  # ITI uses nipāta as minor section
                                "bjt_vagga": current_vagga,
                                "bjt_sutta": sutta_name,
                            }

                            results.append(record)

                elif entry_type == "heading":
                    if "itivuttakapāḷi" in text.lower():
                        current_book = text
                    # Look for nipāta headings like "ekakanipāto"
                    elif "nipāto" in text.lower() and level == 3:
                        current_nipāta = text
                        sutta_counter = 0  # Reset sutta counter for new nipāta
                        last_web_sutta_num = 0
                        current_vagga_for_web = ""
                    # Look for vagga headings like "paṭhamo vaggo"
                    elif "vaggo" in text.lower() and level == 2:
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
    json_file = json_dir / "kn-iti.json"
    output_file = Path(
        "/home/bodhirasa/MyFiles/3_Active/dpd-db/scripts/suttas/bjt/kn4_iti.tsv"
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
