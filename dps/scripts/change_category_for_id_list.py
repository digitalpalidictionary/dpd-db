#!/usr/bin/env python3

"""
Update sbs_category for words from an ID list based on specific conditions
"""

from db.models import PaliWord
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths
from db.get_db_session import get_db_session
from rich.console import Console
import csv
from tools.tic_toc import tic, toc

console = Console()


# Function to read word IDs from a TSV file
def read_ids_from_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        next(tsv_reader)  # Skip header row
        return [int(row[0]) for row in tsv_reader]  # Extracting IDs only from the first column


# Function to remove duplicates from a list
def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [x for x in ordered_ids if not (x in seen or seen.add(x))]
    return ordered_ids_no_duplicates


# Function to derive sutta_identifier from source
def derive_sutta_identifier(source):

    sutta_identifier = ""

    # Iterate through each character in the source string
    for i, char in enumerate(source):
        # capitalize the letter
        sutta_identifier += char.upper()
        # Check if the current character is a letter and the next character is a digit
        # if char.isalpha() and i < len(source) - 1 and source[i + 1].isdigit():
        #     # If yes, insert a space before the letter and capitalize it
        #     sutta_identifier += ""

    return sutta_identifier


# Function to update sbs_category based on a condition function
def update_sbs_category(source, condition_func, message):
    pth = ProjectPaths()
    dpspth = DPSPaths()

    db_session = get_db_session(pth.dpd_db_path)

    # Print the message at the beginning
    console.print(f"[bold bright_yellow]{message}")

    # 1. Fetch the list of word IDs from a file
    ordered_ids = read_ids_from_tsv(dpspth.id_to_add_path)
    
    # 2. Remove duplicates from the list
    unique_ids = remove_duplicates(ordered_ids)

    # Counter for updated rows
    updated_count = 0

    # Derive sutta_identifier from source
    sutta_identifier = derive_sutta_identifier(source)
    # console.print(f"Debugging print of sutta_identifier: {sutta_identifier} for provided source: {source}")

    # 3. Iterate through the IDs and update the database
    for word_id in unique_ids:
        word = db_session.query(PaliWord).filter(PaliWord.id == word_id).first()

        if not word or not word.sbs:
            continue

        if condition_func(word, sutta_identifier) and not word.sbs.sbs_category:
            word.sbs.sbs_category = source
            updated_count += 1
            # db_session.commit()
            print(f"{word.id}")

    console.print(f"[bold green]{updated_count} rows have been updated to {source}.")
    
    db_session.close()


# Condition function to check if all sbs_examples are not empty
def condition_check_all_examples(word, __sutta_identifier__):
    return all([
            getattr(word.sbs, 'sbs_example_1', None),
            getattr(word.sbs, 'sbs_example_2', None),
            getattr(word.sbs, 'sbs_example_3', None),
            getattr(word.sbs, 'sbs_example_4', None)
    ])

# Condition function to check if any sbs_source contains the desired value
def condition_check_source(word, sutta_identifier):
    for i in range(1, 5):
            sbs_source_attr = getattr(word.sbs, f'sbs_source_{i}', None)
            if sbs_source_attr and sutta_identifier in sbs_source_attr:
                return True
    return False


def main():

    tic()

    console.print("[bold blue]Update sbs_category for words from an ID list based on specific conditions")

    # input source eg "sn56" or "mn107" or "sn22" or "sn35"
    source = "sn35"

    # !Update sbs_category based on all examples
    update_sbs_category(source, condition_check_all_examples, "Checking if all examples are present")

    # !Update sbs_category based on sbs_source
    update_sbs_category(source, lambda word, sutta_identifier: condition_check_source(word, sutta_identifier), f"Checking if any sbs_source has {source}")

    toc()

if __name__ == "__main__":
    main()