#!/usr/bin/env python3

"""Un-bold all <b>ca</b> in compound construction"""

from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    for i in db:
        if "<b>ca</b>" in i.compound_construction:
            i.compound_construction = i.compound_construction.replace("<b>ca</b>", "ca")
            print(i.lemma_1, "\t", i.compound_construction)
    db_session.commit()


if __name__ == "__main__":
    main()
