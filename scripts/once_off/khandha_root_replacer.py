#!/usr/bin/env python3

"""Quick starter template for getting a database session and iterating thru."""
import re

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(PaliWord).all()
    for counter, i in enumerate(db):
        if (
            "khandh" in i.pali_1
            and i.root_key
        ):
            i.root_key = "√khandh"
            i.root_sign = "*e"
            i.family_root = i.family_root.replace("√khand", "√khandh")
            i.construction = re.sub("√khand", "√khandh", i.construction)
            print(f"{i.pali_1:30}")
            print(f"{i.root_key:30}")
            print(f"{i.root_sign:30}")
            print(f"{i.family_root:30}")
            print(i.construction)
            print()
    
    db_session.commit()
    


if __name__ == "__main__":
    main()
