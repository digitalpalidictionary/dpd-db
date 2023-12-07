#!/usr/bin/env python3

"""Find duplicate examples in example_1 and example_2"""
import pyperclip

from difflib import SequenceMatcher
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    for i in db:
        if i.example_1 and i.example_2:
            
            # test if identical
            if i.example_1 == i.example_2:
                print(i.pali_1)
                pyperclip.copy(i.pali_1)
                input()

            # test if similar
            elif paragraphs_are_similar(i.example_1, i.example_2):
                print(i.pali_1, end=", ")
                pyperclip.copy(i.pali_1)
                input()



def paragraphs_are_similar(paragraph1, paragraph2, threshold=0.8):
    matcher = SequenceMatcher(None, paragraph1, paragraph2)
    similarity_ratio = matcher.ratio()
    return similarity_ratio >= threshold



if __name__ == "__main__":
    main()
