#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for counter, i in enumerate(db):
        if " vimānavatthu" in i.sutta_1:
            print(i.sutta_1)
            i.sutta_1 = i.sutta_1.replace(" ", "")
            print(i.sutta_1)
        if " vimānavatthu" in i.sutta_2:
            print(i.sutta_2)
            i.sutta_2 = i.sutta_2.replace(" ", "")
            print(i.sutta_2)
    
    # db_session.commit()


if __name__ == "__main__":
    main()
