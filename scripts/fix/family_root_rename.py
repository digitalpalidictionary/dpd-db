#!/usr/bin/env python3

"""Rename a root in the dpd_roots table and dpd_headwords tables """

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword, DpdRoot
from tools.paths import ProjectPaths
from tools.printer import p_title


def main():
    p_title("rename family root")

    before = "√rañj 1"
    after = "√rañj"

    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)

    # ----- rename dpd_roots table -----
    
    roots_query = db_session.query(DpdRoot).filter_by(root=before).first()
    if roots_query:
        roots_query.root = after
        print(roots_query.root)

    # ----- rename dpd_headwords table -----
    
    db = db_session.query(DpdHeadword).all()
    for i in db:
        if i.root_key == before:
            i.root_key = after
            print(i, i.family_root)
    
    db_session.commit()

    


if __name__ == "__main__":
    main()
