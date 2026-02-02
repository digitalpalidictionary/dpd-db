#!/usr/bin/env python3

"""Update the family_word column in DpdHeadword with a new value."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def main():
    pr.tic()
    pr.title("remove word family")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    find: list[str] = [
        "ekadhā",
        "catudhā",
        "chaddhā",
        "chadhā",
        "tidhā",
        "dasadhā",
        "dvidhā",
        "dvedhā",
        "nekadhā 1",
        "nekadhā 2",
        "nekadhā 3",
    ]

    db = db_session.query(DpdHeadword).filter(DpdHeadword.lemma_1.in_(find)).all()

    for i in db:
        print(i.lemma_1, ":", i.family_word, end=" ")
        i.family_word = ""
        print(f"-> '{i.family_word}'")

    db_session.commit()

    pr.toc()


if __name__ == "__main__":
    main()
