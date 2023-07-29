#!/usr/bin/env python3

"""Convery adj, ptp to ptp: pos, grammar and pattern"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord


def main():
    db_session = get_db_session("dpd.db")
    db = db_session.query(PaliWord).all()
    count = 0

    for i in db:
        if "adj, ptp" in i.grammar:
            print(i.pali_1, i.pos, i.grammar, i.pattern)
            i.pos = "ptp"
            i.grammar = i.grammar.replace("adj, ptp", "ptp")
            i.pattern = i.pattern.replace("a adj", "a ptp")
            print(i.pali_1, i.pos, i.grammar, i.pattern)
            print()
            count += 1

    print(count)
    # db_session.commit()
    db_session.close()


if __name__ == "__main__":
    main()
