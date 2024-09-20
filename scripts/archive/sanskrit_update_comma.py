#!/usr/bin/env python3

"""Update commas with backslashes
to show lexical variants in Sanskrit column"""

import pickle

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    # setup db session
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    # load ram's changes to exclude    # 
    with open("db/sanskrit/sanskrit_update_1_backup", "rb") as f:
        sk_dict = pickle.load(f)

    counter = 0
    for i in db:
        if i.id not in sk_dict:
            # replace commas with /
            if "," in i.sanskrit:
                print(i.sanskrit)
                i.sanskrit = i.sanskrit.replace(", ", " / ")
                print(i.sanskrit + "\n")
                counter += 1

    
    # db_session.commit()

if __name__ == "__main__":
    main()
