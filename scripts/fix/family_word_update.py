#!/usr/bin/env python3

"""Update the family_word column in DpdHeadword with a new value."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]update word family")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    find: str = "rudhira"
    replace: str = "rudh"

    for i in db:
        if re.findall(fr"\b{find}\b", str(i.family_word)):
            print(f"[green]{i.lemma_1}")
            print(f"[green]{i.family_word}")
            i.family_word = re.sub(
                fr"\b{find}\b", replace, str(i.family_word))
            print(f"[blue]{i.family_word}")
            print()

    db_session.commit()

    toc()


if __name__ == "__main__":
    main()
