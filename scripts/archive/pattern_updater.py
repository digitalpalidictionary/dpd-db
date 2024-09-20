#!/usr/bin/env python3

"""Update the pattern with a new one."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for counter, i in enumerate(db):
        if (
            i.stem != "-"
            and not i.pattern
        ):  
            last_letter = i.lemma_clean[-1]
            if last_letter == "r":
                pattern = "ar masc"
                # print(f"{i.id:<10}{i.lemma_1:<30}{i.pattern:<20}")
            else:
                pattern = f"{last_letter} masc"

            i.pattern = pattern
            print(f"{i.id:<10}{i.lemma_1:<30}{i.pattern:<20}")
    
    # db_session.commit()


if __name__ == "__main__":
    main()
