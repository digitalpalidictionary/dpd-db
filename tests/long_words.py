#!/usr/bin/env python3

"""Find long words in commentary, example_1 and example_2.
Copy them to the clipboard for hyphenation."""

import re
import pyperclip

from collections import Counter
from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths

maxx = 40

def main():
    print("[bright_yellow]long word finder")
    print(f"[green]{'max length':<15}: {maxx}")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    too_long_list = []
    pattern = rf"\b[\w']{{{maxx},}}\b"
    
    for i in db:
        too_long_list.extend(re.findall(pattern, i.commentary))
        too_long_list.extend(re.findall(pattern, i.example_1))
        too_long_list.extend(re.findall(pattern, i.example_2))

    print(f"[green]{'total found':<15}: {len(too_long_list)}")
    too_long: dict = Counter(too_long_list)
    print(f"[green]{'unique':<15}: {len(too_long)}")

    for word, count in too_long.items():
        print(word, count, end=" ")
        pyperclip.copy(word)
        input()


if __name__ == "__main__":
    main()
