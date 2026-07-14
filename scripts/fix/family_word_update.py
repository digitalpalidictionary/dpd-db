#!/usr/bin/env python3

"""Rename a value in the family_word column of DpdHeadword. Edit FIND/REPLACE
below for the rename you need, run, review the printed matches, then answer
y/n to commit."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

FIND: str = "makuṭa"
REPLACE: str = "makula"


def main() -> None:
    pr.tic()
    pr.yellow_title("update word family")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    found_count = 0
    for i in db:
        if re.findall(rf"\b{FIND}\b", str(i.family_word)):
            found_count += 1
            print(f"[green]{i.lemma_1}")
            print(f"[red]{i.family_word}")
            i.family_word = re.sub(rf"\b{FIND}\b", REPLACE, str(i.family_word))
            print(f"[green]{i.family_word}")
            print()

    if found_count > 0:
        print(f"\n[cyan]{found_count} entries with family_word '{FIND}'")
        print("[green]would you like to commit changes to db? y/n ", end="")
        route = input()
        if route == "y":
            db_session.commit()
            print("[green]committed to db")
        else:
            print("[green]not committed to db")
    else:
        print("\n[green]nothing found")

    pr.toc()


if __name__ == "__main__":
    main()
