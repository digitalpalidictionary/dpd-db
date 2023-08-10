#!/usr/bin/env python3
"""Find the next word from id list and if needed change somthing in database"""

import pyperclip
import csv
from rich import print
from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH
from dps.tools.paths_dps import DPSPaths as DPSPTH


def main():
    print(f"[bright_yellow]Adding words from the {DPSPTH.temp_csv_path}")
    print("[green]Press x to exit")


    # Load IDs from the TSV
    with open(DPSPTH.temp_csv_path, mode='r', encoding='utf-8-sig') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        next(tsv_reader)  # Skip header row
        # Extracting IDs only from the first column
        ordered_ids = [int(row[0]) for row in tsv_reader]
 

    print(f"[blue]Tatal number of IDs fetched: {len(ordered_ids)}[/blue]")  # Print the whole number of fetched IDs

    # Remove duplicates while maintaining order
    seen = set()
    ordered_ids_no_duplicates = []
    for _id in ordered_ids:
        if _id not in seen:
            ordered_ids_no_duplicates.append(_id)
            seen.add(_id)
    ordered_ids = ordered_ids_no_duplicates

    print(f"[blue]Ordered unique IDs fetched: {len(ordered_ids)}[/blue]")  # Print the unique number of fetched IDs

    db_session = get_db_session(PTH.dpd_db_path)

    # Count the total number of words that match the conditions
    total_number = 0
    matching_words = []  # List to store words that match the criteria

    for word_id in ordered_ids:
        word = db_session.query(PaliWord).filter(PaliWord.id == word_id).first()
        if word and (not word.sbs or (word.sbs and not word.sbs.sbs_category)):
            total_number += 1
            matching_words.append(word)  # Storing the word for later use

    if total_number == 0:
        print("[red]No words match the criteria.[/red]")
        return

    else:
        print(f"[yellow]Total words matching criteria: {total_number}[/yellow]")  

    # Display the words in order
    for idx, word in enumerate(matching_words, start=1):
        print(f"{idx}. {word.pali_1}. [cyan]Remaining: {total_number}", end=" ")
        pyperclip.copy(word.pali_1)

        # Update the some column if necessary
        if word.sbs and word.sbs.sbs_class:
            word.sbs.sbs_class = ""

        # Commit the changes to the database
        db_session.commit()

        x = input()
        if x == "x":
            break

        total_number -= 1


if __name__ == "__main__":
    main()