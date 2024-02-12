#!/usr/bin/env python3

"""Cleanup sbs_examples"""

from db.get_db_session import get_db_session
from db.models import DpdHeadwords
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadwords).all()
    for counter, i in enumerate(db):
        if i.sbs:
            if "<br>" in i.sbs.sbs_example_1:
                i.sbs.sbs_example_1 = i.sbs.sbs_example_1.replace("<br>", "\n")
                print(i.sbs.sbs_example_1)
            if "<br>" in i.sbs.sbs_example_2:
                i.sbs.sbs_example_2 = i.sbs.sbs_example_2.replace("<br>", "\n")
                print(i.sbs.sbs_example_2)
            if "<br>" in i.sbs.sbs_example_3:
                i.sbs.sbs_example_3 = i.sbs.sbs_example_3.replace("<br>", "\n")
                print(i.sbs.sbs_example_3)
            if "<br>" in i.sbs.sbs_example_4:
                i.sbs.sbs_example_4 = i.sbs.sbs_example_4.replace("<br>", "\n")
                print(i.sbs.sbs_example_4)
    # db_session.commit()


if __name__ == "__main__":
    main()
