#!/usr/bin/env python3
"""Find the next word from DPS for filling in missing information."""

import pyperclip

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    print("[bright_yellow]adding missing dps words")
    print("[green]press x to exit")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    dpd_db = db_session.query(DpdHeadword).all()

    counter = 0
    dps_set = set()
    for i in dpd_db:
        if (
            not i.meaning_1 and
            i.origin == "dps"
        ):
            dps_set.update([i.lemma_1])
            counter += 1

    done = 0
    for word in dps_set:
        print(f"{counter-done}. {word}", end=" ")
        pyperclip.copy(word)
        done += 1
        x = input()
        if x == "x":
            break


if __name__ == "__main__":
    main()
