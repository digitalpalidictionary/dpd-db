#!/usr/bin/env python3

"""mark all which have sbs_category"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.tic_toc import tic, toc
from tools.paths import ProjectPaths

from sqlalchemy.orm import joinedload

from tools.configger import config_test

def main():
    tic()
    print("[bright_yellow]marking all which have sbs_category changing ebt_count")
    
    if not config_test("dictionary", "show_ebt_count", "yes"):
        print("[green]disabled in config.ini")
        toc()
        return

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    dpd_db = db_session.query(DpdHeadword).options(joinedload(DpdHeadword.sbs)).all()

    for word in dpd_db:
        if word.sbs:
            if word.sbs.sbs_category:
                word.ebt_count = 1
            else:
                word.ebt_count = ""
        else:
            word.ebt_count = ""


    db_session.commit()
    db_session.close()

    toc()


if __name__ == "__main__":
    main()
