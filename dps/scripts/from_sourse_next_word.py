#!/usr/bin/env python3
"""Find the next word from some sourse which do not have ru_meaning yet."""

import pyperclip
from rich import print
from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths as PTH

def main():
    print("[bright_yellow]adding missing words based on conditions")
    source_to_check = input("[blue]Please enter the source string to check (e.g., VIN 1.1.1): ")

    print("[green]press x to exit")
    
    db_session = get_db_session(PTH.dpd_db_path)
    dpd_db = db_session.query(PaliWord).all()

    counter = 0
    words_set = set()

    for i in dpd_db:
        if not i.ru and (
            i.source_1 == source_to_check or i.source_2 == source_to_check
        ):
            words_set.update([i.pali_1])
            counter += 1
    
    done = 0
    for word in words_set:
        print(f"{counter-done}. {word}", end=" ")
        pyperclip.copy(word)
        done += 1
        x = input()
        if x == "x":
            break

if __name__ == "__main__":
    main()
