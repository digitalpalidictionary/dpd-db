#!/usr/bin/env python3
"""Find the next word from id list and if needed change somthing in database"""

import pyperclip
import csv
from rich.console import Console

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths

console = Console()

dpspth = DPSPaths()


NEED_TO_UPDATE = True  # Change this to False if you don't want to update

ORIGINAL_HAS_VALUE = False  # Change this to False if WHAT_TO_UPDATE originally is empty

WHAT_TO_UPDATE = "sbs_category"  # Change this as required


def read_ids_from_tsv(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as tsv_file:
        tsv_reader = csv.reader(tsv_file, delimiter='\t')
        next(tsv_reader)  # Skip header row
        return [int(row[0]) for row in tsv_reader]  # Extracting IDs only from the first column


def remove_duplicates(ordered_ids):
    seen = set()
    ordered_ids_no_duplicates = [x for x in ordered_ids if not (x in seen or seen.add(x))]
    return ordered_ids_no_duplicates


def fetch_matching_words_from_db(db_session, ordered_ids):
    for word_id in ordered_ids:
        word = db_session.query(DpdHeadword).filter(DpdHeadword.id == word_id).first()
        if word and word.sbs:
            attr_value = getattr(word.sbs, WHAT_TO_UPDATE, None)
            if ORIGINAL_HAS_VALUE and attr_value:
                yield word
            elif not ORIGINAL_HAS_VALUE and not attr_value:
                yield word


def display_and_update_word(db_session, word, matching_words_count, input_value):
    print(f"{word.lemma_1}. [cyan]Remaining: {matching_words_count}", end=" ")
    pyperclip.copy(word.lemma_1)

    if NEED_TO_UPDATE and hasattr(word.sbs, WHAT_TO_UPDATE):
            setattr(word.sbs, WHAT_TO_UPDATE, input_value)
            db_session.commit()
            print(f"[green] {WHAT_TO_UPDATE} changed to '' {input_value} ''")

    x = input()
    if x == "x":
        return False
    return True


def main():
    print(f"[bright_yellow]Adding words from the {dpspth.temp_csv_path}")
    console.print("[bold green]Press x to exit")

    ordered_ids = read_ids_from_tsv(dpspth.temp_csv_path)
    print(f"[blue]Total number of IDs fetched: {len(ordered_ids)}[/blue]")

    ordered_ids = remove_duplicates(ordered_ids)
    print(f"[blue]Ordered unique IDs fetched: {len(ordered_ids)}[/blue]")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    matching_word_generator = fetch_matching_words_from_db(db_session, ordered_ids)
    matching_words_count = sum(1 for _ in fetch_matching_words_from_db(db_session, ordered_ids))

    if matching_words_count == 0:
        console.print("[bold red]No words match the criteria.[/red]")
        return

    print(f"[yellow]Total words matching criteria: {matching_words_count}[/yellow]")

    # Only ask for input_value if updates are needed
    input_value = ""
    if NEED_TO_UPDATE:
        input_value = input("Enter the source (e.g. sn56 sn22 sn35 sn12 sn47 sn43): ").strip()

    for word in matching_word_generator:
        if not display_and_update_word(db_session, word, matching_words_count, input_value):
            break
        matching_words_count -= 1

    db_session.close()


if __name__ == "__main__":
    main()
