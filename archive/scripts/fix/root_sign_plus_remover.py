#!/usr/bin/env python3

"""Remove all the `+` in root sign"""

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for counter, i in enumerate(db):
        if "+" in i.root_sign:
            i.root_sign = i.root_sign.replace(" + ", " ")
            print(i.root_sign)
    db_session.commit()


if __name__ == "__main__":
    main()
