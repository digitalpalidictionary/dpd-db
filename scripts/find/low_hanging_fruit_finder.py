#!/usr/bin/env python3

"""Find low hanging fruit = words with examples but no meaning_1."""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.title("low hanging fruit finder")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .filter(DpdHeadword.example_1 != "")
        .all()
    )
    total = len(db_results)
    print(f"{total} words with example and no meaning 1")
    print("press [blue]enter[/blue] to continue or [blue]q[/blue] to quit")

    for index, i in enumerate(db_results):
        print(f"{total} {i.lemma_1}", end=" ")
        pyperclip.copy(i.lemma_1)
        user_input = input()
        if user_input == "q":
            break
        else:
            total -= 1


if __name__ == "__main__":
    main()
