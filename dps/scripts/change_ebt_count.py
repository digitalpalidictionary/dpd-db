#!/usr/bin/env python3

"""mark all which have sbs_category"""

from rich import print

from db.get_db_session import get_db_session
from db.models import PaliWord
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths

from tools.configger import config_test

def main():
    tic()


    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = db_session.query(PaliWord).all()

    for word in dpd_db:
        if word.sbs:
            if word.sbs.sbs_category:
                word.dd.ebt_count = 1
            else:
                word.dd.ebt_count = ""
        else:
            word.dd.ebt_count = ""


    db_session.commit()

    db_session.close()

    toc()


if __name__ == "__main__":
    print("[bright_yellow] mark all which have sbs_category changing ebt_count")
    if config_test("dictionary", "show_ebt_count", "yes"):
        main()
    else:
        print("generating is disabled in the config")
