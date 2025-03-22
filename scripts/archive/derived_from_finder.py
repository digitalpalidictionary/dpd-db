#!/usr/bin/env python3

"""Find derived from which should be empty."""

import re
from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.db_search_string import db_search_string
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()

    list_of = []
    for counter, i in enumerate(db):
        if (
            re.findall(r"\bcomp\b", i.grammar)
            and "of" not in i.grammar
            and "from" not in i.grammar
            and i.derived_from != ""
        ):
            list_of.append(i.id)
    print(db_search_string(list_of))


if __name__ == "__main__":
    main()
