#!/usr/bin/env python3

"""Rename a family_compound/family_idioms entry across all headwords.
Edit find/replace below, then run for each rename job."""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr

find: str = "dissati"
replace: str = "dissati1"


def main() -> None:
    pr.tic()
    pr.yellow_title("update compound family and family idiom")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    for i in db:
        if re.findall(rf"\b{find}\b", str(i.family_compound)):
            print(f"[green]{i.family_compound}")
            i.family_compound = re.sub(rf"\b{find}\b", replace, str(i.family_compound))
            print(f"[blue]{i.family_compound}")
            print()

        if re.findall(rf"\b{find}\b", str(i.family_idioms)):
            print(f"[green]{i.family_idioms}")
            i.family_idioms = re.sub(rf"\b{find}\b", replace, str(i.family_idioms))
            print(f"[blue]{i.family_idioms}")
            print()

    db_session.commit()

    pr.toc()


if __name__ == "__main__":
    main()
