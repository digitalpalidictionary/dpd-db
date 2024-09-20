#!/usr/bin/env python3

"""Regex replace values in phonetic column."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    find = r"^\+(\w)\s*$"
    replace = r"+\1 (Kacc 35, 34)"

    for counter, i in enumerate(db):
        if re.findall(find, i.phonetic, re.MULTILINE):
            print(i.phonetic)
            i.phonetic = re.sub(find, replace, i.phonetic, flags=re.MULTILINE)
            print(i.phonetic)
            print()
            print()
    
    # db_session.commit()


if __name__ == "__main__":
    main()
