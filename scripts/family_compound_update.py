#!/usr/bin/env python3

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]update compound family")
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord).all()

    find = "asana"
    replace = "asana1"

    for i in db:
        if re.findall(fr"\b{find}\b", i.family_compound):
            print(f"[green]{i.family_compound}")
            i.family_compound = re.sub(
                fr"\b{find}\b", replace, i.family_compound)
            print(f"[blue]{i.family_compound}")
            print()

    # db_session.commit()

    toc()


if __name__ == "__main__":
    main()
