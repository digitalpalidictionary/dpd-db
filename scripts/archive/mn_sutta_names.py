#!/usr/bin/env python3

"""Standardize MN sutta names in the database."""

import re

from rich import print
from sqlalchemy.orm.session import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main() -> None:
    pr.tic()
    pr.title("Standardize MN Sutta Names")
    pth: ProjectPaths = ProjectPaths()
    db_session: Session = get_db_session(pth.dpd_db_path)
    db: list[DpdHeadword] = (
        db_session.query(DpdHeadword)
        .filter(DpdHeadword.family_set == "suttas of the Majjhima Nikāya")
        .filter(~DpdHeadword.meaning_1.contains("reference"))
        .all()
    )

    # The regex to capture the three main parts of the meaning string
    # e.g. "Majjhima Nikāya 65; Discourse to Bhaddāli (MN65)"
    pattern = re.compile(r"^(.*?);\s*(.*?)\s*\((.*?)\)$")

    for i in db:
        if not i.meaning_1:
            continue

        match = pattern.match(i.meaning_1)
        if match:
            part1: str = match.group(1).strip()
            part2: str = match.group(2).strip()
            part3: str = match.group(3).strip()

            # Construct the new meaning parts
            new_meaning_1: str = f"{part1} ({part3})"
            new_meaning_2: str = part2

            i.meaning_1 = new_meaning_1
            i.meaning_2 = new_meaning_2

            # The desired output is a list of two strings
            result: list[str] = [new_meaning_1, new_meaning_2]
            print(result)
        else:
            print(f"[red]No match for: {i.meaning_1}")

    db_session.commit()

    pr.toc()


if __name__ == "__main__":
    main()
