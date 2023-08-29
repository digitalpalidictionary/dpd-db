#!/usr/bin/env python3

from db.models import PaliWord
from tools.paths import ProjectPaths as PTH
from db.get_db_session import get_db_session
from rich import print
import re

"""
    Fetch all entries from the database where the `PaliWord.note` contains the string "see ".
    Update the `ru.ru_notes` column with the corresponding format and print the changes.
    Commit the changes to the database.
"""

def get_words_with_see():
    """
    Returns all words with 'see ' in their notes.
    """
    db_session = get_db_session(PTH.dpd_db_path)
    words = db_session.query(PaliWord).filter(PaliWord.notes.contains("see ")).all()
    return words, db_session


def print_complex_see_entries():
    print("[bright_yellow]Printing complex 'see ' entries for review:")

    words_to_check = get_words_with_see()

    for word in words_to_check:
        if not re.match(r"see ([\w\s,§]+)$", word.notes) and not re.search(r"see .*?(in|<i>|\(MW\)|DPPN|SCPN)", word.notes):
            print(f'id {word.id} has notes: "{word.notes}".')
        elif re.search(r"(discuss|definit|suggest)", word.notes):
            print(f'id {word.id} has notes: "{word.notes}".')


def update_ru_notes():
    print("[bright_yellow]Filtering words from db by some condition")

    words_to_update, db_session = get_words_with_see()

    print("[bright_yellow]Changing values")

    for word in words_to_update:
        if (re.match(r"see ([\w\s,§]+)$", word.notes) or re.search(r"see .*?(in|<i>|\(MW\)|DPPN|SCPN)", word.notes)) and not re.search(r"(discuss|definit|suggest)", word.notes):

            after_see = word.notes.split("see ", 1)[1]  # Extract the part after "see "
            
            if word.ru:
                word.ru.ru_notes = f"см. {after_see}"

                # Print changes
                print(f'notes: "{word.notes}" => ru.ru_notes: "{word.ru.ru_notes}"')

    # Commit the changes to the database
    db_session.commit()

    print("[green]What has to be done has been done!")

### !To use the functions:
# print_complex_see_entries()
# update_ru_notes()

