#!/usr/bin/env python3

"""
Copies ru_meaning_raw to ru_meaning for words from an ID list
if ru_meaning_raw is not empty and differs from ru_meaning.
"""

import csv
from sqlalchemy.orm import joinedload
from rich.console import Console

# Assuming Ru model is correctly imported from db.models
from db.models import DpdHeadword, Russian
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.db_helpers import get_db_session
from tools.printer import printer as pr


# Function to read word IDs from a TSV file (copied from change_category_for_id_list.py)
def read_ids_from_tsv(file_path):
    with open(file_path, mode="r", encoding="utf-8-sig") as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter="\t")
        next(tsv_reader)  # Skip header row
        return [
            int(row[0]) for row in tsv_reader
        ]  # Extracting IDs only from the first column


# Function to remove duplicates from a list (copied from change_category_for_id_list.py)
def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [
        x for x in ordered_ids if not (x in seen or seen.add(x))
    ]
    return ordered_ids_no_duplicates


# Function to copy ru_meaning_raw to ru_meaning
def copy_raw_to_meaning(db_session, unique_ids):
    console = Console()
    updated_count = 0
    processed_count = 0
    total_ids = len(unique_ids)

    pr.green(f"Processing {total_ids} unique IDs...")

    for word_id in unique_ids:
        processed_count += 1
        word = (
            db_session.query(DpdHeadword)
            .options(joinedload(DpdHeadword.ru))
            .filter(DpdHeadword.id == word_id)
            .first()
        )

        if word and word.ru and word.ru.ru_meaning_raw:
            # Check 1: Split if main and lit are empty and raw contains separator
            if not word.ru.ru_meaning and not word.ru.ru_meaning_lit and "; досл." in word.ru.ru_meaning_raw:
                parts = word.ru.ru_meaning_raw.split("; досл.", 1)
                if len(parts) == 2:
                    main_meaning = parts[0].strip()
                    lit_meaning = parts[1].strip()
                    pr.white(f"Splitting ID {word.id}: main='{main_meaning}' | lit='{lit_meaning}'")
                    word.ru.ru_meaning = main_meaning
                    word.ru.ru_meaning_lit = lit_meaning
                    updated_count += 1
                    pr.yes("ok")
                else:
                    # Handle unexpected split failure
                    pr.red(f"Warning: ID {word.id} split failed unexpectedly. Raw: '{word.ru.ru_meaning_raw}'")
                    # copy raw to main meaning if main meaning is empty
                    pr.green(f"Updating ID {word.id} (fallback on split fail): '{word.ru.ru_meaning_raw}'")
                    word.ru.ru_meaning = word.ru.ru_meaning_raw
                    updated_count += 1
                    pr.yes("ok")

            elif not word.ru.ru_meaning:
                pr.green(f"Updating ID {word.id} (raw copy): '{word.ru.ru_meaning_raw}'")
                word.ru.ru_meaning = word.ru.ru_meaning_raw
                updated_count += 1
                pr.yes("ok")

        # Print progress periodically
        if processed_count % 1000 == 0:
            pr.green(f"{processed_count}/{total_ids} processed...")

    if updated_count > 0:
        # --- Start of Confirmation Logic ---
        # Use console.print ONLY for the prompt itself for reliable input display
        console.print(f"[bold yellow]Found {updated_count} potential changes.")
        confirm = input("Proceed with committing these changes to the database? (yes/no): ")
        if confirm.lower() == 'yes':
            try:
                pr.green(f"Committing {updated_count} changes...")
                db_session.commit()  # Uncommented commit liney
                pr.green("Changes committed successfully.")
            except Exception as e:
                pr.red(f"[bold red]Error during commit: {e}")
                db_session.rollback()
                pr.red("[bold red]Changes rolled back.")
        # --- End of Confirmation Logic ---
        else:
            pr.red("[bold red]Commit cancelled by user.")
            db_session.rollback()
            pr.red("[bold red]Changes rolled back.")
    else:
        pr.green("No changes needed.")

    pr.green(f"Processed {processed_count} IDs. Updated {updated_count} ru_meaning fields.")
    return updated_count


def main():
    pr.tic()
    pr.green("[bold blue]Copying ru_meaning_raw to ru_meaning for words from ID list")

    pth = ProjectPaths()
    dpspth = DPSPaths()
    db_session = get_db_session(pth.dpd_db_path)

    try:
        id_file_path = dpspth.id_to_add_path
        pr.green(f"Reading IDs from: {id_file_path}")
        ordered_ids = read_ids_from_tsv(id_file_path)
        unique_ids = remove_duplicates(ordered_ids)
        pr.green(f"Found {len(unique_ids)} unique IDs to process.")

        if unique_ids:
            copy_raw_to_meaning(db_session, unique_ids)
        else:
            pr.green("No unique IDs found in the file.")

    except FileNotFoundError:
        pr.red(f"[bold red]Error: ID file not found at {id_file_path}")
    except Exception as e:
        pr.red(f"[bold red]An unexpected error occurred: {e}")
        db_session.rollback() # Rollback in case of error during processing or reading file
    finally:
        db_session.close()
        pr.green("Database session closed.")

    pr.toc()


if __name__ == "__main__":
    main()
