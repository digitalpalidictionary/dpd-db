#!/usr/bin/env python3

"""Find which books have the most missing words"""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .filter(DpdHeadword.example_1 != "")
        .all()
    )

    print(f"{len(db_results)} words with example and no meaning 1: low hanging fruit")
    print()
    for index, i in enumerate(db_results):
        print(f"{index + 1:3n} / {len(db_results)}      {i.id} {i.lemma_1}")
        pyperclip.copy(i.lemma_1)
        input("press any key to continue... ")


if __name__ == "__main__":
    main()
