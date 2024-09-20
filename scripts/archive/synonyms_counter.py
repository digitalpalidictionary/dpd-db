#!/usr/bin/env python3

"""Count all occurences of synonyms in the db."""

from collections import Counter
from rich import print

from db.db_helpers import get_db_session
from db.models import DpdHeadword
from tools.paths import ProjectPaths


def main():
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    db = db_session.query(DpdHeadword).all()
    syns_list = []
    
    for i in db:
        synonyms = i.synonym.split(", ")
        syns_list.extend(synonyms)
    
    syns_count = Counter(syns_list, )

    
    print(syns_count.most_common)


if __name__ == "__main__":
    main()
