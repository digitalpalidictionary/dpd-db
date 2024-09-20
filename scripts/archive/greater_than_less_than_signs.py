#!/usr/bin/env python3

"""Find which fields have greater than and less than signs in them."""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    fields_with_signs = set()

    for counter, i in enumerate(db):
        for attr, value in vars(i).items():
            if "<" in str(value) or ">" in str(value):
                fields_with_signs.add(attr)
    print(fields_with_signs)



if __name__ == "__main__":
    main()
