#!/usr/bin/env python3

"""Find words in commentaries that are not in the lookup table."""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import Lookup
from tools.cst_sc_text_sets import make_cst_text_set
from tools.paths import ProjectPaths
from tools.printer import printer as pr

NIKAYA_COMMENTARY_BOOKS = ["dna", "mna", "sna", "ana"]

def main():
    pr.tic()
    pr.title("commentary words not in lookup table finder")
    
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    
    # 1. get all words from lookup table
    pr.green("getting words from lookup table")
    lookup_db = db_session.query(Lookup.lookup_key).all()
    lookup_set: set[str] = {i.lookup_key for i in lookup_db}
    pr.yes(len(lookup_set))
    
    # 2. make a set of all words in commentary books
    commentary_words: set[str] = make_cst_text_set(pth, NIKAYA_COMMENTARY_BOOKS)
    
    # 3. find which words in the commentaries are NOT in the lookup table
    pr.green("finding missing words")
    missing_words: set[str] = commentary_words - lookup_set
    pr.yes(len(missing_words))
    
    # 4. print them out one by one, enter to continue, copying each word to the clipboard
    missing_words_sorted = sorted(list(missing_words))
    total = len(missing_words_sorted)
    
    print(f"found {total} missing words")
    print("press [blue]enter[/blue] to copy next word, or [blue]q[/blue] to quit")
    
    for index, word in enumerate(missing_words_sorted):
        print(f"{index + 1:>5} / {total:<5} {word}", end=" ", flush=True)
        pyperclip.copy(word)
        user_input = input()
        if user_input.lower() == "q":
            break

    pr.toc()

if __name__ == "__main__":
    main()
