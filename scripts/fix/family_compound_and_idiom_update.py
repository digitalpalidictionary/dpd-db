#!/usr/bin/env python3

"""Update the family_compound and family_idioms column in DpdHeadword with a new value."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc


def main():
    tic()
    print("[bright_yellow]update compound family and family idiom")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    find: str = "acchariya"
    replace: str ="acchara"

    for i in db:
        if re.findall(fr"\b{find}\b", str(i.family_compound)):
            print(f"[green]{i.family_compound}")
            i.family_compound = re.sub(
                fr"\b{find}\b", replace, str(i.family_compound))
            print(f"[blue]{i.family_compound}")
            print()

        if re.findall(fr"\b{find}\b", str(i.family_idioms)):
            print(f"[green]{i.family_idioms}")
            i.family_idioms = re.sub(
                fr"\b{find}\b", replace, str(i.family_idioms))
            print(f"[blue]{i.family_idioms}")
            print()

    db_session.commit()

    toc()


if __name__ == "__main__":
    main()
