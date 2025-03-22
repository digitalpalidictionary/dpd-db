#!/usr/bin/env python3

"""Find low hanging fruit = words with examples but no meaning_1."""

import pyperclip
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import p_title


def main():
    p_title("low hanging fruit finder")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db_results = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.meaning_1 == "")
        .filter(DpdHeadword.example_1 != "")
        .all()
    )

    print(f"{len(db_results)} words with example and no meaning 1")
    print()
    for index, i in enumerate(db_results):
        print(f"{index + 1:3n} / {len(db_results)} {i.lemma_1}")
        pyperclip.copy(i.lemma_1)
        input("press any key to continue... ")


if __name__ == "__main__":
    main()
