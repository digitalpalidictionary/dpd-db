#!/usr/bin/env python3

"""Fix all the dealbreakers which break exporter code."""
import sys
from rich import print
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.tic_toc import tic, toc
from tools.pos import POS

def main():
    tic()
    print("[bright_yellow]fixing dealbreakers")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    apostrophe_in_key_fields(db_session)
    
    ok = pos_not_in_pos(db_session)
    if not ok:
        sys.exit(1)
    toc()


def pos_not_in_pos(db_session):
    """Check that pos in db match pos in theory."""
    print(f"[green]{'finding wrong pos':<30} ")

    ok = True
    result = db_session.query(DpdHeadword).all()
    for r in result:
        if r.pos not in POS:
            print(f"[red]{'wrong pos found':<20}{r.pos:<10}[bright_red][white]{r.lemma_1}")
            ok = False
    if not ok:
        return False
    else:
        return True


def apostrophe_in_key_fields(db_session):
    """Find apostrophes in key fields:
    - lemma_1
    - lemma_2
    - stem
    """
    print(f"[green]{'fixing apostrophe in key fields':<30} ", end="")
    found = 0

    # lemma_1
    results = db_session \
        .query(DpdHeadword) \
        .filter(DpdHeadword.lemma_1.contains("'", )) \
        .all()
    for r in results:
        r.lemma_1 = r.lemma_1.replace("'", "")
        found += 1

    # lemma_2
    results = db_session \
        .query(DpdHeadword) \
        .filter(DpdHeadword.lemma_2.contains("'", )) \
        .all()
    for r in results:
        r.lemma_2 = r.lemma_2.replace("'", "")
        found += 1

    # stem
    results = db_session \
        .query(DpdHeadword) \
        .filter(DpdHeadword.stem.contains("'", )) \
        .all()
    for r in results:
        r.stem = r.stem.replace("'", "")
        found += 1

    db_session.commit()
    print(found)

if __name__ == "__main__":
    main()
