#!/usr/bin/env python3

"""Fix all the dealbreakers which break exporter code."""
from rich import print
from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc

def main():
    tic()
    print("[bright_yellow]fixing dealbreakers")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    print(f"[green]{'fixing apostrophe in key fields':<30} ", end="")
    found = apostrophe_in_key_fields(db_session)
    print(found)

    toc()


def apostrophe_in_key_fields(db_session):
    """Find apostrophes in key fields:
    - pali_1
    - pali_2
    - stem
    """

    found = 0

    # pali_1
    results = db_session \
        .query(PaliWord) \
        .filter(PaliWord.pali_1.contains("'", )) \
        .all()
    for r in results:
        r.pali_1 = r.pali_1.replace("'", "")
        found += 1

    # pali_2
    results = db_session \
        .query(PaliWord) \
        .filter(PaliWord.pali_2.contains("'", )) \
        .all()
    for r in results:
        r.pali_2 = r.pali_2.replace("'", "")
        found += 1

    # stem
    results = db_session \
        .query(PaliWord) \
        .filter(PaliWord.stem.contains("'", )) \
        .all()
    for r in results:
        r.stem = r.stem.replace("'", "")
        found += 1

    db_session.commit()
    return found

if __name__ == "__main__":
    main()
