#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.meaning_construction import summarize_construction


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()

    test_cases = [
        "duddada",
        "duddama",
        "duddasa",
        "duddasika",
        "niddara",
        "niddarathaṃ",
        "niddasa",
        "sududdasa"
    ]

    for counter, i in enumerate(db):
        if (
            i.pali_1 in test_cases
            # and i.meaning_1
            # and i.pos == "fut"
            # and i.construction.startswith("ku ")
            # and i.root_base
        ):
            construction = summarize_construction(i)
            if (
                ">" in construction
                or " + +" in construction
                or "/n" in construction
                or "[" in construction
                or "(" in construction
            ):
                print("[red]error")
            print(f"{i.pali_1:<20}[cyan]{construction}")


if __name__ == "__main__":
    main()
