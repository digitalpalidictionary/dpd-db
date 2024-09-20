#!/usr/bin/env python3

"""Make a list of all pos in DPD."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    pos_set = set()
    for counter, i in enumerate(db):
        if i.pos not in pos_set:
            pos_set.add(i.pos)

    pos_list = sorted(pos_set)
    print(pos_list)

if __name__ == "__main__":
    main()
