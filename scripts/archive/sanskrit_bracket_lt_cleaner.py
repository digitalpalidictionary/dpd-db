#!/usr/bin/env python3

"""Clean (< ) from Sanskrit."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    counter = 0
    for i in db:
        if "(<" in i.sanskrit:
            print(i.lemma_1)
            print(i.sanskrit)
            sk_clean = re.sub(r"\(<(.+?)\)", "< \\1", i.sanskrit)
            i.sanskrit = sk_clean
            print(i.sanskrit)
            print()
            counter += 1
    print(counter)
    db_session.commit()

if __name__ == "__main__":
    main()
