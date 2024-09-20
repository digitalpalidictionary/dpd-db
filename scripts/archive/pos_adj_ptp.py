#!/usr/bin/env python3

"""Convery adj, ptp to ptp: pos, grammar and pattern"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 0

    for i in db:
        if "adj, ptp" in i.grammar:
            print(i.lemma_1, i.pos, i.grammar, i.pattern)
            i.pos = "ptp"
            i.grammar = i.grammar.replace("adj, ptp", "ptp")
            if i.pattern is not None:
                i.pattern = i.pattern.replace("a adj", "a ptp")
            print(i.lemma_1, i.pos, i.grammar, i.pattern)
            print()
            count += 1

    print(count)
    # db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
