#!/usr/bin/env python3

"""Check and sync family_compound and family_idioms.

Reports mismatches where family_compound differs from family_idioms,
then fills any empty family_idioms with the family_compound value.
"""

import re

from sqlalchemy.orm import Session

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths
from tools.printer import printer as pr


def find_mismatches(db: list[DpdHeadword]) -> list[str]:
    """Find entries where family_compound and family_idioms differ."""
    not_equal: list[str] = []
    for i in db:
        if (
            not re.findall(r"\bcomp\b", i.grammar)
            and i.pos not in ["idiom", "sandhi"]
            and i.family_compound
            and " " not in i.family_compound
            and i.family_idioms
            and i.family_idioms != i.family_compound
        ):
            not_equal.append(i.lemma_1)
    return not_equal


def fill_empty_idioms(db: list[DpdHeadword], db_session: Session) -> int:
    """Fill empty family_idioms with family_compound. Returns count of fills."""
    counter = 0
    for i in db:
        if (
            not re.findall(r"\bcomp\b", i.grammar)
            and i.pos not in ["idiom", "sandhi"]
            and i.family_compound
            and " " not in i.family_compound
            and not i.family_idioms
        ):
            i.family_idioms = i.family_compound
            counter += 1
    db_session.commit()
    return counter


def main() -> None:
    pr.tic()
    pr.yellow_title("finding difference between family_compound and family_idioms")

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    not_equal = find_mismatches(db)
    pr.summary("family_compound != family_idioms", len(not_equal))
    if not_equal:
        print(db_search_string(not_equal))
        pr.toc()
        return

    counter = fill_empty_idioms(db, db_session)
    pr.summary("family_idioms empty", counter)
    pr.toc()


if __name__ == "__main__":
    main()
