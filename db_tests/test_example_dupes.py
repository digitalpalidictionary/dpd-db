#!/usr/bin/env python3

"""Find duplicate examples in example_1 and example_2"""
import pyperclip

from difflib import SequenceMatcher
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths

threshold=0.82

def main():
    print("[bright_yellow]find duplicate or similar examples")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for i in db:
        if i.example_1 and i.example_2:
            
            # test if identical
            if i.example_1 == i.example_2:
                print(i.lemma_1)
                pyperclip.copy(i.lemma_1)
                input()

            # test if similar
            elif paragraphs_are_similar(i.example_1, i.example_2):
                print()
                print(f"{i.id:<10}{i.lemma_1}")
                print(f"[dark_green]{i.source_1} {i.sutta_1}")
                print(f"[green]{i.example_1}")
                print(f"[blue]{i.source_2} {i.sutta_2}")
                print(f"[cyan]{i.example_2}")
                pyperclip.copy(i.lemma_1)
                user_input = input("d=delete, s=swap ")
                if user_input == "d":
                    i = delete_example_2(i)
                    db_session.commit()
                    print("[red]example_2 deleted")
                elif user_input == "s":
                    i = swop_example_1_and_2(i)
                    i = delete_example_2(i)
                    db_session.commit()
                    print("[red]example_2 swapped")

def delete_example_2(i):
    i.source_2 = ""
    i.sutta_2 = ""
    i.example_2 = ""
    return i

def swop_example_1_and_2(i):
    i.source_1 = i.source_2
    i.sutta_1 = i.sutta_2
    i.example_1 = i.example_2
    return i




def paragraphs_are_similar(paragraph1, paragraph2, threshold=threshold):
    matcher = SequenceMatcher(None, paragraph1, paragraph2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold



if __name__ == "__main__":
    main()
