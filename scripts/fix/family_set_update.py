#!/usr/bin/env python3

"""Update the family_set column in DpdHeadword with a new value."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]update family set")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    find: str = "nipāta"
    replace: str = "indeclinables"

    for i in db:
        if re.findall(
            fr"\b{find}\b", str(i.family_set)):
            print(f"[green]{i.lemma_1}")
            print(f"[green]{i.family_set}")
            i.family_set = re.sub(
                fr"\b{find}\b", replace, str(i.family_set))
            print(f"[blue]{i.family_set}")
            print()

    db_session.commit()

    toc()


if __name__ == "__main__":
    main()
