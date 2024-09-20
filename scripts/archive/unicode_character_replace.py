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
    # character = "\u0061\u0304" # ā
    # character = "\u0075\u0304"  # ū
    character = "ṁ"
    replacement = "ṃ"
    for i in db:
        for field in i.__dict__.keys():
            if isinstance(getattr(i, field), str):
                if character in getattr(i, field):
                    setattr(i, field, getattr(i, field).replace(character, replacement))
                    print(getattr(i, field))
        
    # db_session.commit()


if __name__ == "__main__":
    main()
