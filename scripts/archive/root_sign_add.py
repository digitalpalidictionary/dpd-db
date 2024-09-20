#!/usr/bin/env python3

"""Add missing root sign."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    headwords = []
    for i in db:
        if (
            i.meaning_1 and
            i.root_key and
            not i.root_sign
        ):
            i.root_sign = i.rt.root_sign
            print(f"{i.lemma_1:<20}{i.root_key:<10}{i.root_sign}")
            headwords.append(i.lemma_1)

    db_session.commit()
    db_session.close()
    print(db_search_string(headwords))


if __name__ == "__main__":
    main()
