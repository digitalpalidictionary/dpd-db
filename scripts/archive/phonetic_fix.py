#!/usr/bin/env python3

"""Fix missing plus sign in phonetic column."""

import re
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for i in db:
        if re.findall(r"^\w \(Kacc 35, 34\)", i.phonetic, re.MULTILINE):
            print(i.phonetic)
            i.phonetic = f"+{i.phonetic}"
            print(i.phonetic)
            print()

    db_session.commit()


if __name__ == "__main__":
    main()
