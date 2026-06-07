#!/usr/bin/env python3

"""Find all Sanskrit sūtra not ending with (bsk)"""

import re

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def is_candidate(i: DpdHeadword) -> bool:
    if (
        re.findall(r"sutta\b", i.lemma_1)
        and i.sanskrit.endswith("sūtra")
        and "sūtra (bsk)" not in i.sanskrit
    ):
        return True
    return False


def is_dupe(i: DpdHeadword) -> bool:
    if "sūtra (bsk)" in i.sanskrit:
        return True
    return False


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    count = 1
    for counter, i in enumerate(db):
        if is_candidate(i):
            sanskrit_sub = re.sub(r"sūtra$", "sūtra (bsk)", i.sanskrit)
            i.sanskrit = sanskrit_sub
            print(count, i.lemma_1, sanskrit_sub)
            count += 1
        if is_dupe(i):
            print(count, i.lemma_1, i.sanskrit)
            count += 1

    # db_session.commit()


if __name__ == "__main__":
    main()
