#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 0
    for counter, i in enumerate(db):
        if "(<" in i.sanskrit:
            print(i.sanskrit)
            i.sanskrit = re.sub(r"\((<.[^()]*)\)", "\\1", i.sanskrit)
            print(i.sanskrit)
            print()
            count += 1
    
    # db_session.commit()
    print(count)


if __name__ == "__main__":
    main()
