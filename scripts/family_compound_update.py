#!/usr/bin/env python3

"""Update the family_compound column in PaliWord with a new value."""

import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]update compound family")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    find: str = "papaṭika"
    replace: str ="papaṭikā"

    for i in db:
        if re.findall(fr"\b{find}\b", str(i.family_compound)):
            print(f"[green]{i.family_compound}")
            i.family_compound = re.sub(
                fr"\b{find}\b", replace, str(i.family_compound))
            print(f"[blue]{i.family_compound}")
            print()

    db_session.commit()

    toc()


if __name__ == "__main__":
    main()
