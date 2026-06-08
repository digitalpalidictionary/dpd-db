#!/usr/bin/env python3

"""Fix all the dealbreakers which break exporter code."""

import sys
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths
from tools.printer import printer as pr
from tools.pos import POS
from sqlalchemy.orm import Session


def main() -> None:
    pr.tic()
    pr.yellow_title("fixing dealbreakers")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    apostrophe_in_key_fields(db_session)

    ok = pos_not_in_pos(db_session)
    if not ok:
        sys.exit(1)
    pr.toc()


def pos_not_in_pos(db_session: Session) -> bool:
    """Check that pos in db match pos in theory."""
    pr.green_tmr("finding wrong pos")
    invalid = db_session.query(DpdHeadword).filter(~DpdHeadword.pos.in_(POS)).all()
    for r in invalid:
        pr.red(f"wrong pos found: {r.pos:<10}{r.lemma_1}")
    if invalid:
        pr.no("errors")
        return False
    pr.yes("ok")
    return True


def apostrophe_in_key_fields(db_session: Session) -> None:
    """Find apostrophes in key fields:
    - lemma_1
    - lemma_2
    - stem
    """
    pr.green_tmr("fixing apostrophe in key fields")
    found = 0

    results = (
        db_session.query(DpdHeadword)
        .filter(
            DpdHeadword.lemma_1.contains("'")
            | DpdHeadword.lemma_2.contains("'")
            | DpdHeadword.stem.contains("'")
        )
        .all()
    )
    for r in results:
        if "'" in r.lemma_1:
            r.lemma_1 = r.lemma_1.replace("'", "")
            found += 1
        if "'" in r.lemma_2:
            r.lemma_2 = r.lemma_2.replace("'", "")
            found += 1
        if "'" in r.stem:
            r.stem = r.stem.replace("'", "")
            found += 1

    db_session.commit()
    pr.yes(str(found))


if __name__ == "__main__":
    main()
